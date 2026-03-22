from datetime import datetime, timezone, timedelta

SP = timezone(timedelta(hours=-3))


def format_capture(
    source_type: str,
    extracted_text: str = "",
    context: str = "",
    link: str = "",
    thumbnail: str = "",
) -> tuple[str, str]:
    """Returns (filename, markdown_content)."""
    now = datetime.now(SP)
    timestamp = now.strftime("%Y-%m-%d_%H%M")
    date_display = now.strftime("%d/%m/%Y %H:%M")

    filename = f"{timestamp}.md"

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
