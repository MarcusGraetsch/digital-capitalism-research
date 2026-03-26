#!/usr/bin/env python3
"""
Newsletter Parser - Extract structured article entries from newsletter emails.
Detects common newsletter formats (Substack, Mailchimp, Revue, beehiiv, etc.)
and extracts individual article blocks with headline, link, and teaser text.
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse


# Known newsletter sender patterns
NEWSLETTER_SENDERS = {
    'substack': ['@substack.com', 'noreply@substack.com'],
    'mailchimp': ['@mail.mailchimp.com', '@mailchimp.com', 'mc.sendgrid.net'],
    'beehiiv': ['@beehiiv.com', '@mail.beehiiv.com'],
    'revue': ['@getrevue.co', 'noreply@getrevue.co'],
    'buttondown': ['@buttondown.email'],
    'convertkit': ['@convertkit.com', '@ck.page'],
    'ghost': ['@ghost.io'],
}

# URL patterns to skip (tracking, unsubscribe, social)
SKIP_URL_PATTERNS = [
    'unsubscribe', 'manage-preferences', 'view-in-browser',
    'tracking', 'click.', 'list-manage.com', 'mailchimp.com/track',
    'open.substack.com', 'email.mg.', 'trk.', 'utm_source',
    'facebook.com', 'twitter.com', 'x.com', 'linkedin.com',
    'instagram.com', 'youtube.com', 'mailto:',
    'privacy-policy', 'terms-of-service', 'impressum',
]


class NewsletterArticle:
    """A single article extracted from a newsletter"""
    def __init__(self, url, headline=None, teaser=None, source_newsletter=None):
        self.url = url
        self.headline = headline or ''
        self.teaser = teaser or ''
        self.source_newsletter = source_newsletter or ''

    def __repr__(self):
        return f"NewsletterArticle({self.headline[:40]}... -> {self.url[:60]})"


def detect_newsletter_type(sender_email, html_content=''):
    """Detect which newsletter platform sent this email"""
    sender_lower = sender_email.lower()

    for platform, patterns in NEWSLETTER_SENDERS.items():
        if any(p in sender_lower for p in patterns):
            return platform

    # Check HTML content for platform signatures
    html_lower = html_content.lower() if html_content else ''
    if 'substack.com' in html_lower:
        return 'substack'
    if 'mailchimp.com' in html_lower or 'mc.us' in html_lower:
        return 'mailchimp'
    if 'beehiiv.com' in html_lower:
        return 'beehiiv'
    if 'ghost.io' in html_lower or 'ghost.org' in html_lower:
        return 'ghost'

    return 'generic'


def is_article_url(url):
    """Check if a URL looks like an article link (not tracking/admin)"""
    url_lower = url.lower()
    if any(pattern in url_lower for pattern in SKIP_URL_PATTERNS):
        return False
    # Must be http(s)
    if not url_lower.startswith('http'):
        return False
    # Skip very short URLs (likely redirects/trackers)
    parsed = urlparse(url)
    if len(parsed.path) < 2 and not parsed.query:
        return False
    return True


def parse_substack(soup, sender):
    """Parse Substack newsletter format"""
    articles = []

    # Substack posts have the main article in the email body
    # External links are usually in <a> tags within the content
    post_body = soup.find('div', class_='body') or soup.find('div', class_='post-body')
    if not post_body:
        post_body = soup

    # Look for linked headlines (h1, h2, h3 with <a> children)
    for heading in post_body.find_all(['h1', 'h2', 'h3']):
        link = heading.find('a', href=True)
        if link and is_article_url(link['href']):
            teaser = ''
            next_p = heading.find_next_sibling('p')
            if next_p:
                teaser = next_p.get_text(strip=True)[:200]
            articles.append(NewsletterArticle(
                url=link['href'],
                headline=heading.get_text(strip=True),
                teaser=teaser,
                source_newsletter=sender
            ))

    # Also collect standalone article links in paragraphs
    for a_tag in post_body.find_all('a', href=True):
        url = a_tag['href']
        if is_article_url(url) and not any(art.url == url for art in articles):
            text = a_tag.get_text(strip=True)
            if text and len(text) > 5:
                articles.append(NewsletterArticle(
                    url=url,
                    headline=text,
                    source_newsletter=sender
                ))

    return articles


def parse_mailchimp(soup, sender):
    """Parse Mailchimp newsletter format"""
    articles = []

    # Mailchimp uses table-based layouts with content blocks
    # Look for content sections with links
    content_blocks = soup.find_all('td', class_=re.compile('mc.*content|bodyContent'))
    if not content_blocks:
        content_blocks = [soup]

    for block in content_blocks:
        # Find headline + link pairs
        for heading in block.find_all(['h1', 'h2', 'h3', 'h4']):
            link = heading.find('a', href=True)
            if not link:
                # Check if next sibling has a "read more" link
                next_el = heading.find_next_sibling()
                if next_el:
                    link = next_el.find('a', href=True)

            if link and is_article_url(link['href']):
                teaser = ''
                next_p = heading.find_next('p')
                if next_p:
                    teaser = next_p.get_text(strip=True)[:200]
                articles.append(NewsletterArticle(
                    url=link['href'],
                    headline=heading.get_text(strip=True),
                    teaser=teaser,
                    source_newsletter=sender
                ))

    return articles


def parse_generic(soup, sender):
    """Generic newsletter parser - works for most formats"""
    articles = []
    seen_urls = set()

    # Strategy 1: Find headline elements linked to articles
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        link = heading.find('a', href=True)
        if link and is_article_url(link['href']) and link['href'] not in seen_urls:
            seen_urls.add(link['href'])
            teaser = ''
            next_p = heading.find_next_sibling('p')
            if next_p:
                teaser = next_p.get_text(strip=True)[:200]
            articles.append(NewsletterArticle(
                url=link['href'],
                headline=heading.get_text(strip=True),
                teaser=teaser,
                source_newsletter=sender
            ))

    # Strategy 2: Find "read more" / "weiterlesen" style links
    read_more_patterns = re.compile(
        r'(read more|weiterlesen|more|lesen|continue reading|full article|zum artikel)',
        re.IGNORECASE
    )
    for a_tag in soup.find_all('a', href=True, string=read_more_patterns):
        url = a_tag['href']
        if is_article_url(url) and url not in seen_urls:
            seen_urls.add(url)
            # Walk backwards to find a headline
            headline = ''
            prev = a_tag.find_previous(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])
            if prev:
                headline = prev.get_text(strip=True)
            articles.append(NewsletterArticle(
                url=url,
                headline=headline,
                source_newsletter=sender
            ))

    # Strategy 3: Collect remaining substantial links
    for a_tag in soup.find_all('a', href=True):
        url = a_tag['href']
        text = a_tag.get_text(strip=True)
        if (is_article_url(url) and url not in seen_urls
                and text and len(text) > 10
                and not read_more_patterns.search(text)):
            seen_urls.add(url)
            articles.append(NewsletterArticle(
                url=url,
                headline=text,
                source_newsletter=sender
            ))

    return articles


def parse_newsletter(html_content, sender_email='', subject=''):
    """
    Main entry point: parse a newsletter email and extract article entries.

    Args:
        html_content: The HTML body of the email
        sender_email: The From address
        subject: The email subject line

    Returns:
        List of NewsletterArticle objects
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove tracking pixels, style, script
    for tag in soup(['script', 'style', 'img']):
        if tag.name == 'img' and tag.get('width') == '1':
            tag.decompose()
        elif tag.name != 'img':
            tag.decompose()

    newsletter_type = detect_newsletter_type(sender_email, html_content)

    parsers = {
        'substack': parse_substack,
        'mailchimp': parse_mailchimp,
    }

    parser_func = parsers.get(newsletter_type, parse_generic)
    articles = parser_func(soup, sender_email)

    # If platform-specific parser found nothing, fall back to generic
    if not articles and parser_func != parse_generic:
        articles = parse_generic(soup, sender_email)

    return articles


def is_newsletter_email(sender_email, html_content=''):
    """Quick check: does this email look like a newsletter?"""
    sender_lower = sender_email.lower()

    # Known newsletter platforms
    for patterns in NEWSLETTER_SENDERS.values():
        if any(p in sender_lower for p in patterns):
            return True

    # Common newsletter sender patterns
    newsletter_hints = [
        'newsletter', 'digest', 'noreply', 'no-reply',
        'news@', 'updates@', 'info@', 'hello@',
    ]
    if any(hint in sender_lower for hint in newsletter_hints):
        return True

    return False
