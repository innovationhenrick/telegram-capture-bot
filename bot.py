import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_TOKEN, ALLOWED_CHAT_IDS, INBOX_PATH
from processors.text import process_text
from processors.link import extract_urls, fetch_meta
from formatter import format_capture
from github_client import commit_file

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def authorized(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS:
            await update.message.reply_text("Acesso negado.")
            return
        return await func(update, context)
    return wrapper


def _save_to_github(filename: str, content: str, source: str) -> tuple[bool, str]:
    path = f"{INBOX_PATH}/{filename}"
    success = commit_file(
        path=path,
        content=content,
        message=f"capture: {source} via telegram",
    )
    return success, path


@authorized
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot de captura ativo.\n\n"
        "Envie texto ou links e eu salvo direto no Obsidian.\n"
        "Responda a mensagem de confirmacao com contexto extra.\n\n"
        "/start - mostra esta mensagem"
    )


@authorized
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if not text.strip():
        return

    urls = extract_urls(text)

    if urls:
        url = urls[0]
        meta = fetch_meta(url)
        title = meta.get("title", "") or url
        extracted = title
        if meta.get("description"):
            extracted += f"\n\n{meta['description']}"

        filename, content = format_capture(
            source_type="link",
            extracted_text=extracted,
            link=url,
            thumbnail=meta.get("image", ""),
            title=title,
        )

        success, path = _save_to_github(filename, content, "link")

        if success:
            context.user_data["last_save"] = {
                "filename": filename,
                "content": content,
                "source": "link",
                "title": title,
                "link": url,
                "thumbnail": meta.get("image", ""),
            }
            await update.message.reply_text(
                f"Salvo: {title}\n`{path}`\n\nResponda com contexto extra se quiser.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("Erro ao salvar. Tente novamente.")
    else:
        clean = process_text(text)
        first_line = clean.split("\n")[0][:80]

        filename, content = format_capture(
            source_type="texto",
            extracted_text=clean,
            title=first_line,
        )

        success, path = _save_to_github(filename, content, "texto")

        if success:
            context.user_data["last_save"] = {
                "filename": filename,
                "content": content,
                "source": "texto",
                "title": first_line,
            }
            await update.message.reply_text(
                f"Salvo: {first_line}\n`{path}`\n\nResponda com contexto extra se quiser.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("Erro ao salvar. Tente novamente.")


@authorized
async def handle_reply_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    last = context.user_data.get("last_save")
    if not last:
        await handle_message(update, context)
        return

    extra_context = (update.message.text or "").strip()
    if not extra_context:
        return

    filename, content = format_capture(
        source_type=last["source"],
        extracted_text=last.get("content", "").split("**Texto extraído:**\n")[-1].split("\n---")[0] if "**Texto extraído:**" in last.get("content", "") else last.get("title", ""),
        context=extra_context,
        link=last.get("link", ""),
        thumbnail=last.get("thumbnail", ""),
        title=last.get("title", ""),
    )

    success, path = _save_to_github(filename, content, last["source"])

    if success:
        context.user_data["last_save"]["content"] = content
        await update.message.reply_text(
            f"Atualizado com contexto: `{path}`",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("Erro ao atualizar. Tente novamente.")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(
        filters.REPLY & filters.TEXT & ~filters.COMMAND,
        handle_reply_context,
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message,
    ))

    logger.info("Bot iniciado")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
