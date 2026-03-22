import re
from datetime import datetime, timezone, timedelta

SP = timezone(timedelta(hours=-3))


def slugify(text: str, max_len: int = 60) -> str:
    """Turn text into a filesystem-safe slug."""
    text = text.strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    if len(text) > max_len:
        text = text[:max_len].rsplit("-", 1)[0]
    return text or "captura"


def format_capture(
    source_type: str,
    extracted_text: str = "",
    context: str = "",
    link: str = "",
    thumbnail: str = "",
    title: str = "",
) -> tuple[str, str]:
    """Returns (filename, markdown_content)."""
    now = datetime.now(SP)
    timestamp = now.strftime("%Y-%m-%d_%H%M")
    date_display = now.strftime("%d/%m/%Y %H:%M")

    name_base = title or extracted_text.split("\n")[0] or "captura"
    slug = slugify(name_base)
    filename = f"{timestamp}_{slug}.md"

    parts = [f"## Captura - {date_display}\n"]

    if source_type:
        parts.append(f"**Fonte:** {source_type}")

    if link:
        parts.append(f"**Link:** {link}")

    if thumbnail:
        parts.append(f"**Thumbnail:** ![]({thumbnail})")

    if extracted_text:
        parts.append(f"\n**Texto extraído:**\n{extracted_text}")

    if context:
        parts.append(f"\n**Contexto:**\n{context}")

    parts.append("\n---\n*Tags: #captura #inbox*")

    content = "\n".join(parts)
    return filename, content
