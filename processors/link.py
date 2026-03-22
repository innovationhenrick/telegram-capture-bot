import re
import requests
from bs4 import BeautifulSoup


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s<>\"']+", text)


def fetch_meta(url: str) -> dict:
    """Fetch Open Graph metadata from a URL."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        def og(prop):
            tag = soup.find("meta", property=f"og:{prop}")
            if tag:
                return tag.get("content", "")
            return ""

        title = og("title") or (soup.title.string if soup.title else "")
        description = og("description")
        image = og("image")

        return {
            "title": (title or "").strip(),
            "description": (description or "").strip(),
            "image": (image or "").strip(),
        }
    except Exception:
        return {"title": url, "description": "", "image": ""}
