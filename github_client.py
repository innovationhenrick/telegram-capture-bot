import base64
import logging
import requests
from config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH

logger = logging.getLogger(__name__)


def commit_file(path: str, content: str, message: str) -> bool:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    logger.info("Commit to %s", path)

    existing_sha = None
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        existing_sha = resp.json().get("sha")

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": GITHUB_BRANCH,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    resp = requests.put(url, headers=headers, json=payload)
    logger.info("GitHub response: %s %s", resp.status_code, resp.text[:500])
    return resp.status_code in (200, 201)
