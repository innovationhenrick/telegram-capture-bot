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


@authorized
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot de captura ativo.\n\n"
        "Envie texto ou links e eu salvo no seu Obsidian.\n"
        "Responda uma captura com contexto extra antes de salvar.\n\n"
        "Comandos:\n"
        "/salvar - salva a ultima captura pendente\n"
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
        extracted = meta.get("title", "")
        if meta.get("description"):
            extracted += f"\n\n{meta['description']}"

        filename, content = format_capture(
            source_type="link",
            extracted_text=extracted,
            link=url,
            thumbnail=meta.get("image", ""),
        )

        context.user_data["pending"] = {
            "filename": filename,
            "content": content,
            "source": "link",
        }

        preview = f"Link capturado: {meta.get('title', url)}\n\nResponda com contexto ou /salvar para gravar."
        await update.message.reply_text(preview)
    else:
        clean = process_text(text)
        filename, content = format_capture(
            source_type="texto",
            extracted_text=clean,
        )

        context.user_data["pending"] = {
            "filename": filename,
            "content": content,
            "source": "texto",
        }

        preview = f"Texto capturado ({len(clean)} chars).\n\nResponda com contexto ou /salvar para gravar."
        await update.message.reply_text(preview)


@authorized
async def handle_reply_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    pending = context.user_data.get("pending")
    if not pending:
        await handle_message(update, context)
        return

    extra_context = update.message.text or ""
    if not extra_context.strip():
        return

    filename, content = format_capture(
        source_type=pending["source"],
        extracted_text=pending["content"].split("**Texto extraído:**\n")[-1].split("\n---")[0] if "**Texto extraído:**" in pending["content"] else "",
        context=extra_context.strip(),
        link=_extract_link(pending["content"]),
        thumbnail=_extract_thumbnail(pending["content"]),
    )

    context.user_data["pending"] = {
        "filename": filename,
        "content": content,
        "source": pending["source"],
    }

    await update.message.reply_text("Contexto adicionado. /salvar para gravar.")


def _extract_link(content: str) -> str:
    for line in content.split("\n"):
        if line.startswith("**Link:**"):
            return line.replace("**Link:**", "").strip()
    return ""


def _extract_thumbnail(content: str) -> str:
    for line in content.split("\n"):
        if line.startswith("**Thumbnail:**"):
            url = line.replace("**Thumbnail:**", "").strip()
            if url.startswith("![](") and url.endswith(")"):
                return url[4:-1]
            return url
    return ""


@authorized
async def salvar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending = context.user_data.get("pending")
    if not pending:
        await update.message.reply_text("Nenhuma captura pendente.")
        return

    path = f"{INBOX_PATH}/{pending['filename']}"
    success = commit_file(
        path=path,
        content=pending["content"],
        message=f"capture: {pending['source']} via telegram",
    )

    if success:
        context.user_data.pop("pending", None)
        await update.message.reply_text(f"Salvo em `{path}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("Erro ao salvar. Tente novamente.")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("salvar", salvar))

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
