import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_REPO = os.environ.get("GITHUB_REPO", "innovationhenrick/obsidian")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
ALLOWED_CHAT_IDS = [
    int(cid.strip())
    for cid in os.environ.get("ALLOWED_CHAT_IDS", "").split(",")
    if cid.strip()
]
INBOX_PATH = os.environ.get("INBOX_PATH", "inbox")
