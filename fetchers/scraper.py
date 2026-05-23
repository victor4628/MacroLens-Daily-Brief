import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Known paywall / unscrappable domains — skip immediately
BLOCKED_DOMAINS = {
    "bloomberg.com", "wsj.com", "ft.com",
    "barrons.com", "economist.com",
}


def _is_blocked(url: str) -> bool:
    return any(domain in url for domain in BLOCKED_DOMAINS)


def fetch_article_text(url: str, max_chars: int = 3000) -> str:
    """
    Fetch and extract the main body text of a news article.
    Returns empty string on failure (paywall, timeout, parse error, etc.)
    """
    if not url or _is_blocked(url):
        return ""

    try:
        from bs4 import BeautifulSoup

        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "header", "footer",
                         "aside", "figure", "figcaption", "noscript",
                         "iframe", "button", "form"]):
            tag.decompose()

        # Try semantic article containers first
        content = (
            soup.find("article")
            or soup.find("main")
            or soup.find(attrs={"class": lambda c: c and "article-body" in " ".join(c)})
            or soup.find(attrs={"class": lambda c: c and "story-body" in " ".join(c)})
            or soup.body
        )

        if not content:
            return ""

        paragraphs = [
            p.get_text(" ", strip=True)
            for p in content.find_all("p")
            if len(p.get_text(strip=True)) > 40  # skip very short fragments
        ]

        text = " ".join(paragraphs)
        return text[:max_chars]

    except Exception:
        return ""


def fetch_articles_concurrent(news_items: list[dict],
                               max_workers: int = 6) -> dict[str, str]:
    """
    Concurrently fetch full text for a list of news dicts.
    Returns {url: full_text} mapping. Empty string means scraping failed.
    """
    results: dict[str, str] = {}
    urls = [n.get("url", "") for n in news_items]

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_url = {pool.submit(fetch_article_text, url): url for url in urls if url}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception:
                results[url] = ""

    return results
