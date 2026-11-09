"""Batch web scraping — free, local, no API keys, no credits.

Replaces paid batch-scraping APIs with two pieces we already have:

- ``httpx.AsyncClient`` for concurrent HTTP fetching (HTTP/2, connection pooling)
- ``trafilatura`` for main-content extraction to Markdown

Design notes
------------
**A finished batch does not mean every page was saved.** A batch run
reports per-URL status; only pages with actually extracted content count
as success. Anything else keeps its error reason. Callers must look at
``stats`` instead of assuming success.

**Politeness is enforced, not assumed:**

- ``robots.txt`` is fetched once per domain and honoured via
  ``urllib.robotparser`` (cached).
- Per-domain concurrency cap and a minimum delay between two requests to
  the same domain, so a burst never hammers one host.
- A global concurrency cap bounds total open sockets.

**Content only.** trafilatura strips navigation, boilerplate and (unless
requested) comments. That is what makes the output usable for text
analysis, and it is why the result is Markdown rather than raw HTML.

Usage::

    from researchclaw.web.batch_scraper import BatchScraper

    async with BatchScraper(max_concurrency=16) as scraper:
        results = await scraper.scrape_many(urls)
        print(results.stats)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "ResearchClaw/0.5 (Academic Research Bot; +batch-scraper)"
DEFAULT_MAX_CONCURRENCY = 16
DEFAULT_PER_DOMAIN_CONCURRENCY = 2
DEFAULT_PER_DOMAIN_DELAY = 1.0
DEFAULT_TIMEOUT = 25.0
DEFAULT_MAX_RETRIES = 2
MIN_CONTENT_CHARS = 200
ROBOTS_TIMEOUT = 10.0

# Status codes worth retrying: transient server/network conditions.
RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525}

# 429 means "you are too fast". Retrying immediately makes it worse, so the
# domain is put on cooldown and its request spacing is widened.
DEFAULT_429_BACKOFF = 5.0
# Obergrenze fuer die Cooldown-Dauer. labournet.de fragt per Retry-After
# 15 Minuten — das ist die Frist, die der Server uns gibt, und sie muss
# eingehalten werden. Wer sie ignoriert, wird geblockt statt gedrosselt.
MAX_429_BACKOFF = 900.0
MAX_ADAPTIVE_DELAY = 30.0
DEFAULT_ADAPTIVE_DELAY = 0.0

# Circuit breaker: after N throttles a domain is skipped entirely for the
# rest of the run. A throttled host usually blocks the IP, so hammering it
# with further requests only wastes the run's time budget.
DEFAULT_429_STRIKES = 3
DEFAULT_BREAKER_COOLDOWN = 300.0

# A domain that keeps dropping the connection (timeout, reset) is not
# throttling us — it simply does not serve us. Retrying every remaining URL
# of that domain only burns the run's time budget: a single hung URL costs
# timeout x retries, and the chunk cannot finish before all of them are done.
DEFAULT_MAX_FAIL_STRIKES = 3
DEFAULT_FAIL_BREAKER_COOLDOWN = 900.0


def _parse_retry_after(value: str | None) -> float | None:
    """Parse a ``Retry-After`` header.

    RFC 9110 allows two forms: delta-seconds ("120") and an HTTP-date
    ("Mon, 09 Nov 2026 15:24:38 +0000"). Real hosts use both — nginx in
    front of labournet.de sends the date form. Ignoring it means ignoring
    the cooldown the server asked for, which is exactly how a 429 turns into
    a block.
    """
    if not value:
        return None
    raw = value.strip()
    try:
        seconds = float(raw)
    except (TypeError, ValueError):
        pass
    else:
        if seconds < 0:
            return None
        return min(seconds, MAX_429_BACKOFF)

    try:
        from email.utils import parsedate_to_datetime

        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    delta = (when - datetime.now(timezone.utc)).total_seconds()
    if delta < 0:
        # The date is in the past — retry immediately.
        return 0.0
    return min(delta, MAX_429_BACKOFF)


@dataclass
class FetchResult:
    """Raw HTTP outcome for one URL."""

    url: str
    status_code: int | None = None
    html: str = ""
    error: str = ""
    elapsed_seconds: float = 0.0
    from_cache: bool = False
    retry_after: float | None = None


@dataclass
class ExtractResult:
    """Markdown extraction outcome for one URL."""

    url: str
    markdown: str = ""
    title: str = ""
    word_count: int = 0
    status_code: int | None = None
    error: str = ""
    elapsed_seconds: float = 0.0

    @property
    def success(self) -> bool:
        """True only when real content was extracted."""
        return bool(self.markdown) and self.word_count > 0

    @property
    def content_status(self) -> str:
        """Status label matching the articles.content_status vocabulary."""
        if self.success:
            return "success"
        if self.error.startswith("robots"):
            return "blocked"
        if self.status_code == 403:
            return "paywall"
        if self.status_code in (401, 402):
            return "paywall"
        if self.status_code and self.status_code != 200:
            # 404 = tot, 429 = gedrosselt, 5xx = Serverfehler
            return f"http_{self.status_code}"
        if self.status_code == 200:
            # Die Antwort kam, aber der Inhalt liess sich nicht extrahieren.
            return "too_short"
        if self.error:
            # Kein HTTP-Status: Timeout, Verbindungsabbruch, DNS-Fehler.
            # Das ist ein Fehler, kein "zu kurzer Inhalt".
            return "error"
        return "too_short"


@dataclass
class ScrapeStats:
    """Aggregate counters for one batch run."""

    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped_robots: int = 0
    elapsed_seconds: float = 0.0
    by_status: dict[str, int] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    def record(self, result: ExtractResult) -> None:
        self.total += 1
        if result.success:
            self.succeeded += 1
        else:
            self.failed += 1
            if result.error:
                self.errors[result.url] = result.error
        label = result.content_status
        self.by_status[label] = self.by_status.get(label, 0) + 1

    @property
    def success_rate(self) -> float:
        return (self.succeeded / self.total) if self.total else 0.0

    def summary(self) -> str:
        return (
            f"{self.succeeded}/{self.total} ok "
            f"({self.success_rate:.1%}), {self.failed} failed, "
            f"{self.skipped_robots} robots-blocked, {self.elapsed_seconds:.1f}s"
        )


class BatchScraper:
    """Concurrent scraper: fetch with httpx, extract with trafilatura.

    Parameters
    ----------
    max_concurrency:
        Maximum number of simultaneous requests overall.
    per_domain_concurrency:
        Maximum simultaneous requests to a single host.
    per_domain_delay:
        Minimum seconds between two requests to the same host.
    respect_robots:
        When True (default) robots.txt is fetched and honoured.
    """

    def __init__(
        self,
        *,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        per_domain_concurrency: int = DEFAULT_PER_DOMAIN_CONCURRENCY,
        per_domain_delay: float = DEFAULT_PER_DOMAIN_DELAY,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        respect_robots: bool = True,
        user_agent: str = DEFAULT_USER_AGENT,
        max_429_strikes: int = DEFAULT_429_STRIKES,
        breaker_cooldown: float = DEFAULT_BREAKER_COOLDOWN,
        max_fail_strikes: int = DEFAULT_MAX_FAIL_STRIKES,
        fail_breaker_cooldown: float = DEFAULT_FAIL_BREAKER_COOLDOWN,
        respect_crawl_delay: bool = True,
    ) -> None:
        self.max_concurrency = max_concurrency
        self.per_domain_concurrency = per_domain_concurrency
        self.per_domain_delay = per_domain_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.respect_robots = respect_robots
        self.user_agent = user_agent
        self.max_429_strikes = max_429_strikes
        self.breaker_cooldown = breaker_cooldown
        self.max_fail_strikes = max_fail_strikes
        self.fail_breaker_cooldown = fail_breaker_cooldown
        self.respect_crawl_delay = respect_crawl_delay

        self._global_sem = asyncio.Semaphore(max_concurrency)
        self._domain_429_strikes: dict[str, int] = {}
        self._domain_breaker: dict[str, float] = {}
        self._domain_fail_strikes: dict[str, int] = {}
        self._domain_fail_breaker: dict[str, float] = {}
        self._domain_crawl_delay: dict[str, float] = {}
        self._domain_sems: dict[str, asyncio.Semaphore] = {}
        self._domain_locks: dict[str, asyncio.Lock] = {}
        self._domain_last: dict[str, float] = {}
        self._domain_cooldown: dict[str, float] = {}
        self._domain_adaptive_delay: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser | None] = {}
        self._robots_locks: dict[str, asyncio.Lock] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def scrape_many(self, urls: list[str]) -> list[ExtractResult]:
        """Scrape all URLs concurrently and return one result per URL.

        The returned list preserves the input order.
        """
        t0 = time.monotonic()
        results = await asyncio.gather(
            *(self.scrape(url) for url in urls), return_exceptions=True
        )
        out: list[ExtractResult] = []
        for url, res in zip(urls, results):
            if isinstance(res, BaseException):
                out.append(ExtractResult(url=url, error=f"{type(res).__name__}: {res}"))
            else:
                out.append(res)
        stats = ScrapeStats(elapsed_seconds=time.monotonic() - t0)
        for r in out:
            stats.record(r)
        self.last_stats = stats
        return out

    async def scrape(self, url: str) -> ExtractResult:
        """Scrape a single URL."""
        t0 = time.monotonic()
        domain = _domain_of(url)
        if self.respect_robots and not await self._robots_allows(url):
            return ExtractResult(
                url=url, error="robots.txt disallows this path", elapsed_seconds=time.monotonic() - t0
            )

        fetch = await self._fetch(url)
        if fetch.error or not fetch.html:
            return ExtractResult(
                url=url,
                status_code=fetch.status_code,
                error=fetch.error or "empty response",
                elapsed_seconds=time.monotonic() - t0,
            )

        extracted = self._extract(fetch.html, url)
        extracted.status_code = fetch.status_code
        extracted.elapsed_seconds = time.monotonic() - t0
        return extracted

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------

    async def _fetch(self, url: str) -> FetchResult:
        """Fetch one URL with retries and per-domain politeness.

        Rate limiting (429) is handled specially: the server's
        ``Retry-After`` is honoured, the domain goes on cooldown, and its
        request spacing is widened so the next request is not the one that
        gets throttled again.
        """
        domain = _domain_of(url)
        sem = self._domain_semaphore(domain)

        async with self._global_sem:
            async with sem:
                last_error = ""
                last_status: int | None = None
                last_retry_after: float | None = None
                backoff = DEFAULT_429_BACKOFF
                for attempt in range(self.max_retries + 1):
                    # The breaker is checked per attempt, not once per URL:
                    # all URLs of a chunk enter this queue at the same time, so
                    # a check in scrape() would pass every one of them before
                    # the first 429 even arrives.
                    if self._breaker_open(domain):
                        return FetchResult(
                            url=url,
                            status_code=429,
                            error="circuit breaker open: domain throttled repeatedly",
                        )
                    if self._fail_breaker_open(domain):
                        return FetchResult(
                            url=url,
                            error="fail breaker open: domain unreachable (timeouts/connection errors)",
                        )
                    await self._respect_domain_delay(domain)
                    result = await self._fetch_once(url)
                    if not result.error:
                        self._note_success(domain)
                        return result
                    last_error = result.error
                    last_status = result.status_code
                    last_retry_after = result.retry_after
                    if result.status_code is None:
                        # Timeout, DNS-Fehler, Verbindungsabbruch: der Host
                        # antwortet gar nicht. Ein Retry kostet nur erneut
                        # timeout Sekunden — und bei 12 URLs derselben Domain
                        # blockiert das den Chunk minutenlang. Also: zaehlen,
                        # aber nicht wiederholen.
                        self._note_failed(domain)
                        return result
                    if result.status_code == 429:
                        wait = result.retry_after if result.retry_after is not None else backoff
                        self._note_throttled(domain, wait)
                        if attempt < self.max_retries:
                            await asyncio.sleep(wait)
                            backoff = min(backoff * 2, MAX_429_BACKOFF)
                        continue
                    if result.status_code not in RETRYABLE_STATUS and result.status_code is not None:
                        return result
                    if attempt < self.max_retries:
                        await asyncio.sleep(1.5 * (2**attempt))
                return FetchResult(
                    url=url,
                    status_code=last_status,
                    error=last_error,
                    retry_after=last_retry_after,
                )

    def _note_throttled(self, domain: str, wait: float) -> None:
        """Put a domain on cooldown and widen its request spacing."""
        self._domain_cooldown[domain] = time.monotonic() + wait
        current = self._domain_adaptive_delay.get(domain, DEFAULT_ADAPTIVE_DELAY)
        self._domain_adaptive_delay[domain] = min(
            max(current * 2, self.per_domain_delay * 2), MAX_ADAPTIVE_DELAY
        )
        strikes = self._domain_429_strikes.get(domain, 0) + 1
        self._domain_429_strikes[domain] = strikes
        logger.info(
            "domain %s throttled (429) — cooldown %.1fs, spacing now %.1fs (strike %d/%d)",
            domain, wait, self._domain_adaptive_delay[domain], strikes, self.max_429_strikes,
        )
        if strikes >= self.max_429_strikes:
            # Der Breaker darf nie kuerzer laufen als die vom Server
            # verlangte Wartezeit — sonst requestet man die Domain erneut,
            # obwohl der Host noch gesperrt hat.
            cooldown = max(self.breaker_cooldown, wait)
            self._domain_breaker[domain] = time.monotonic() + cooldown
            logger.warning(
                "domain %s circuit breaker open for %.0fs — remaining URLs are skipped",
                domain, cooldown,
            )

    def _note_failed(self, domain: str) -> None:
        """Count a non-HTTP failure (timeout, reset, DNS) for the domain."""
        strikes = self._domain_fail_strikes.get(domain, 0) + 1
        self._domain_fail_strikes[domain] = strikes
        if strikes >= self.max_fail_strikes:
            self._domain_fail_breaker[domain] = time.monotonic() + self.fail_breaker_cooldown
            logger.warning(
                "domain %s unreachable %d times — skipping it for %.0fs",
                domain, strikes, self.fail_breaker_cooldown,
            )

    def _fail_breaker_open(self, domain: str) -> bool:
        """True while a domain is skipped because it does not answer us."""
        until = self._domain_fail_breaker.get(domain)
        if until is None:
            return False
        if time.monotonic() >= until:
            self._domain_fail_breaker.pop(domain, None)
            self._domain_fail_strikes.pop(domain, None)
            return False
        return True

    def _breaker_open(self, domain: str) -> bool:
        """True while the domain is skipped because it kept throttling us."""
        until = self._domain_breaker.get(domain)
        if until is None:
            return False
        if time.monotonic() >= until:
            self._domain_breaker.pop(domain, None)
            self._domain_429_strikes.pop(domain, None)
            return False
        return True

    def _note_success(self, domain: str) -> None:
        """Relax a domain's spacing again after a successful request."""
        self._domain_429_strikes.pop(domain, None)
        self._domain_fail_strikes.pop(domain, None)
        current = self._domain_adaptive_delay.get(domain)
        if current is None:
            return
        relaxed = max(self.per_domain_delay, current / 2)
        self._domain_adaptive_delay[domain] = relaxed
        if relaxed <= self.per_domain_delay:
            self._domain_adaptive_delay.pop(domain, None)

    async def _fetch_once(self, url: str) -> FetchResult:
        import httpx

        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "de,en;q=0.8",
                },
            ) as client:
                resp = await client.get(url)
                html = resp.text
                return FetchResult(
                    url=url,
                    status_code=resp.status_code,
                    html=html if resp.status_code == 200 else "",
                    error="" if resp.status_code == 200 else f"HTTP {resp.status_code}",
                    elapsed_seconds=time.monotonic() - t0,
                    retry_after=_parse_retry_after(resp.headers.get("Retry-After")),
                )
        except Exception as exc:  # noqa: BLE001
            return FetchResult(
                url=url, error=f"{type(exc).__name__}: {exc}", elapsed_seconds=time.monotonic() - t0
            )

    async def _respect_domain_delay(self, domain: str) -> None:
        """Wait so that two requests to the same host are spaced apart.

        Honours an active cooldown (set after a 429) and the adaptive
        spacing that the domain has earned.
        """
        lock = self._domain_lock(domain)
        async with lock:
            cooldown_until = self._domain_cooldown.get(domain)
            if cooldown_until is not None:
                wait = cooldown_until - time.monotonic()
                if wait > 0:
                    await asyncio.sleep(wait)
                self._domain_cooldown.pop(domain, None)

            spacing = self._domain_adaptive_delay.get(domain, self.per_domain_delay)
            crawl_delay = self._domain_crawl_delay.get(domain, 0.0)
            if crawl_delay > spacing:
                spacing = crawl_delay
            last = self._domain_last.get(domain)
            if last is not None:
                wait = spacing - (time.monotonic() - last)
                if wait > 0:
                    await asyncio.sleep(wait)
            self._domain_last[domain] = time.monotonic()

    def _domain_semaphore(self, domain: str) -> asyncio.Semaphore:
        if domain not in self._domain_sems:
            self._domain_sems[domain] = asyncio.Semaphore(self.per_domain_concurrency)
        return self._domain_sems[domain]

    def _domain_lock(self, domain: str) -> asyncio.Lock:
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        return self._domain_locks[domain]

    # ------------------------------------------------------------------
    # robots.txt
    # ------------------------------------------------------------------

    async def _robots_allows(self, url: str) -> bool:
        """Check robots.txt for one URL (cached per domain)."""
        domain = _domain_of(url)
        if domain not in self._robots:
            async with self._robots_lock(domain):
                if domain not in self._robots:
                    self._robots[domain] = await self._load_robots(domain)
        parser = self._robots.get(domain)
        if parser is None:
            return True
        try:
            return parser.can_fetch(self.user_agent, url)
        except Exception:  # noqa: BLE001
            return True

    def _robots_lock(self, domain: str) -> asyncio.Lock:
        if domain not in self._robots_locks:
            self._robots_locks[domain] = asyncio.Lock()
        return self._robots_locks[domain]

    async def _load_robots(self, domain: str) -> RobotFileParser | None:
        """Fetch and parse robots.txt. None means 'no restriction known'."""
        import httpx

        url = f"https://{domain}/robots.txt"
        try:
            async with httpx.AsyncClient(
                timeout=ROBOTS_TIMEOUT, follow_redirects=True,
                headers={"User-Agent": self.user_agent},
            ) as client:
                resp = await client.get(url)
        except Exception as exc:  # noqa: BLE001
            logger.debug("robots.txt for %s unreachable: %s", domain, exc)
            return None

        if resp.status_code != 200 or not resp.text.strip():
            return None

        parser = RobotFileParser()
        parser.parse(resp.text.splitlines())
        self._remember_crawl_delay(domain, parser)
        return parser

    def _remember_crawl_delay(self, domain: str, parser: RobotFileParser) -> None:
        """Honour ``Crawl-Delay`` from robots.txt.

        Hosts like labournet.de ask for 20s between requests. Ignoring that
        is not "polite but slow" — it is a violation of the site's stated
        limit, and it is also what earns an IP block.
        """
        if not self.respect_crawl_delay:
            return
        delay = None
        for ua in (self.user_agent, "*"):
            try:
                delay = parser.crawl_delay(ua)
            except Exception:  # noqa: BLE001
                delay = None
            if delay:
                break
        if delay:
            self._domain_crawl_delay[domain] = float(delay)
            logger.info("domain %s requests Crawl-Delay %.0fs", domain, float(delay))

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def _extract(self, html: str, url: str) -> ExtractResult:
        """Extract main content as Markdown."""
        try:
            import trafilatura
        except ImportError:
            return ExtractResult(url=url, error="trafilatura not installed")

        try:
            markdown = trafilatura.extract(
                html,
                url=url,
                output_format="markdown",
                include_comments=False,
                include_tables=True,
                favor_recall=True,
                no_fallback=False,
            )
        except Exception as exc:  # noqa: BLE001
            return ExtractResult(url=url, error=f"extract failed: {exc}")

        if not markdown or len(markdown.strip()) < MIN_CONTENT_CHARS:
            return ExtractResult(
                url=url, error="content too short", word_count=len(markdown.split()) if markdown else 0
            )

        return ExtractResult(
            url=url,
            markdown=markdown.strip(),
            title=_extract_title(html),
            word_count=len(markdown.split()),
        )


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _domain_of(url: str) -> str:
    return (urlparse(url).netloc or url).lower()


def _extract_title(html: str) -> str:
    """Best-effort title from <title> or og:title."""
    try:
        from lxml import html as lxml_html

        tree = lxml_html.fromstring(html)
        og = tree.xpath("//meta[@property='og:title']/@content")
        if og and og[0].strip():
            return og[0].strip()
        titles = tree.xpath("//title/text()")
        if titles and titles[0].strip():
            return titles[0].strip()
    except Exception:  # noqa: BLE001
        pass
    return ""


def markdown_to_frontmatter_body(markdown: str) -> str:
    """Strip a leading YAML frontmatter block from markdown."""
    if not markdown.startswith("---"):
        return markdown
    parts = markdown.split("---", 2)
    return parts[2].lstrip("\n") if len(parts) == 3 else markdown
