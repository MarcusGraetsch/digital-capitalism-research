"""Tests for researchclaw.web.batch_scraper — BatchScraper.

Focus: the parts that decide whether a scraped page counts as success.
The scraper must never report a page as saved when no real content was
extracted, and it must stay polite towards the target host.
"""

from __future__ import annotations

import asyncio

from researchclaw.web.batch_scraper import (
    BatchScraper,
    ExtractResult,
    FetchResult,
    ScrapeStats,
    _domain_of,
    _extract_title,
    markdown_to_frontmatter_body,
)


# ---------------------------------------------------------------------------
# ExtractResult
# ---------------------------------------------------------------------------


class TestExtractResult:
    def test_success_requires_markdown_and_words(self):
        r = ExtractResult(url="u", markdown="hello", word_count=5)
        assert r.success

    def test_no_markdown_is_not_success(self):
        r = ExtractResult(url="u", markdown="", word_count=0)
        assert not r.success

    def test_zero_words_is_not_success(self):
        r = ExtractResult(url="u", markdown="   ", word_count=0)
        assert not r.success

    def test_status_success(self):
        r = ExtractResult(url="u", markdown="x", word_count=3)
        assert r.content_status == "success"

    def test_status_http_404_not_too_short(self):
        r = ExtractResult(url="u", status_code=404, error="HTTP 404")
        assert r.content_status == "http_404"

    def test_status_http_429(self):
        r = ExtractResult(url="u", status_code=429, error="HTTP 429")
        assert r.content_status == "http_429"

    def test_status_http_503(self):
        r = ExtractResult(url="u", status_code=503, error="HTTP 503")
        assert r.content_status == "http_503"

    def test_status_paywall_on_403(self):
        r = ExtractResult(url="u", status_code=403, error="HTTP 403")
        assert r.content_status == "paywall"

    def test_status_robots_blocked(self):
        r = ExtractResult(url="u", error="robots.txt disallows this path")
        assert r.content_status == "blocked"

    def test_status_too_short_when_200_but_no_content(self):
        r = ExtractResult(url="u", status_code=200, error="content too short")
        assert r.content_status == "too_short"


# ---------------------------------------------------------------------------
# ScrapeStats
# ---------------------------------------------------------------------------


class TestScrapeStats:
    def test_counts_success_and_failure(self):
        stats = ScrapeStats()
        stats.record(ExtractResult(url="a", markdown="x", word_count=3))
        stats.record(ExtractResult(url="b", status_code=404, error="HTTP 404"))
        assert stats.total == 2
        assert stats.succeeded == 1
        assert stats.failed == 1

    def test_success_rate(self):
        stats = ScrapeStats()
        stats.record(ExtractResult(url="a", markdown="x", word_count=3))
        stats.record(ExtractResult(url="b", status_code=404))
        assert stats.success_rate == 0.5

    def test_empty_stats_zero_rate(self):
        assert ScrapeStats().success_rate == 0.0

    def test_by_status_counts(self):
        stats = ScrapeStats()
        stats.record(ExtractResult(url="a", status_code=404))
        stats.record(ExtractResult(url="b", status_code=404))
        stats.record(ExtractResult(url="c", markdown="x", word_count=3))
        assert stats.by_status["http_404"] == 2
        assert stats.by_status["success"] == 1

    def test_errors_recorded_only_for_failures(self):
        stats = ScrapeStats()
        stats.record(ExtractResult(url="ok", markdown="x", word_count=3))
        stats.record(ExtractResult(url="bad", status_code=500, error="boom"))
        assert "bad" in stats.errors
        assert "ok" not in stats.errors

    def test_summary_mentions_counts(self):
        stats = ScrapeStats()
        stats.record(ExtractResult(url="a", markdown="x", word_count=3))
        assert "1/1" in stats.summary()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_domain_of(self):
        assert _domain_of("https://www.example.com/a/b") == "www.example.com"

    def test_domain_of_lowercases(self):
        assert _domain_of("https://Example.COM/x") == "example.com"

    def test_extract_title_from_title_tag(self):
        html = "<html><head><title>Hello</title></head><body></body></html>"
        assert _extract_title(html) == "Hello"

    def test_extract_title_prefers_og_title(self):
        html = (
            "<html><head><title>T</title>"
            "<meta property='og:title' content='OG'></head></html>"
        )
        assert _extract_title(html) == "OG"

    def test_extract_title_handles_broken_html(self):
        assert _extract_title("<<<not html") == ""

    def test_markdown_to_frontmatter_body_strips_frontmatter(self):
        md = "---\nkey: val\n---\n\n# Title\n\nBody"
        body = markdown_to_frontmatter_body(md)
        assert body.startswith("# Title")
        assert "key: val" not in body

    def test_markdown_to_frontmatter_body_keeps_plain_text(self):
        assert markdown_to_frontmatter_body("# Title") == "# Title"


# ---------------------------------------------------------------------------
# BatchScraper behaviour
# ---------------------------------------------------------------------------


class TestBatchScraper:
    def test_per_domain_semaphore_is_reused(self):
        s = BatchScraper()
        a = s._domain_semaphore("example.com")
        b = s._domain_semaphore("example.com")
        assert a is b

    def test_per_domain_semaphore_differs_per_domain(self):
        s = BatchScraper()
        assert s._domain_semaphore("a.com") is not s._domain_semaphore("b.com")

    def test_extract_returns_markdown(self):
        html = (
            "<html><head><title>T</title></head><body><article>"
            + "<p>" + ("Ein Absatz mit Inhalt. " * 30) + "</p>"
            + "</article></body></html>"
        )
        s = BatchScraper()
        res = s._extract(html, "https://example.com/a")
        assert res.success
        assert res.word_count > 10
        assert res.title == "T"

    def test_extract_fails_on_empty_body(self):
        s = BatchScraper()
        res = s._extract("<html><body></body></html>", "https://example.com/a")
        assert not res.success
        assert res.error

    def test_extract_handles_malformed_html(self):
        s = BatchScraper()
        res = s._extract("<<<broken", "https://example.com/a")
        assert not res.success

    def test_scrape_many_preserves_order(self, monkeypatch):
        s = BatchScraper()
        urls = [f"https://example.com/{i}" for i in range(5)]

        async def fake_fetch(url):
            await asyncio.sleep(0.01)
            idx = int(url.rsplit("/", 1)[1])
            return FetchResult(url=url, status_code=200, html="<p>x</p>")

        monkeypatch.setattr(s, "_fetch", fake_fetch)
        results = asyncio.run(s.scrape_many(urls))
        assert [r.url for r in results] == urls

    def test_scrape_many_reports_failures_without_raising(self, monkeypatch):
        s = BatchScraper()

        async def fake_fetch(url):
            raise RuntimeError("network down")

        monkeypatch.setattr(s, "_fetch", fake_fetch)
        results = asyncio.run(s.scrape_many(["https://example.com/a"]))
        assert len(results) == 1
        assert not results[0].success
        assert "RuntimeError" in results[0].error

    def test_scrape_blocks_when_robots_disallows(self, monkeypatch):
        s = BatchScraper(respect_robots=True)

        async def fake_robots(url):
            return False

        monkeypatch.setattr(s, "_robots_allows", fake_robots)
        res = asyncio.run(s.scrape("https://example.com/private"))
        assert not res.success
        assert "robots" in res.error
        assert res.content_status == "blocked"

    def test_scrape_reports_http_error_status(self, monkeypatch):
        s = BatchScraper(respect_robots=False)

        async def fake_fetch(url):
            return FetchResult(url=url, status_code=404, error="HTTP 404")

        monkeypatch.setattr(s, "_fetch", fake_fetch)
        res = asyncio.run(s.scrape("https://example.com/missing"))
        assert res.status_code == 404
        assert res.content_status == "http_404"
