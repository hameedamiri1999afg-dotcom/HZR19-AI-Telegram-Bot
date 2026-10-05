import os
import re
import asyncio
import hashlib
from urllib.parse import quote

import aiohttp
from aiohttp import web

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# ============================================================
# HZR19 CONFIG
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
RENDER_EXTERNAL_URL = os.getenv(
    "RENDER_EXTERNAL_URL",
    "https://hzr19-ai-telegram-bot.onrender.com"
)

WEBHOOK_PATH = "/telegram/webhook"
WEBHOOK_URL = RENDER_EXTERNAL_URL.rstrip("/") + WEBHOOK_PATH

BRAND = "𝕳𝖅𝕽𝟏⁹"
FOOTER = "@m19_goat"

# Short temporary storage for search results.
# It prevents Telegram callback_data from becoming too long.
SEARCH_RESULTS = {}

# Short conversation memory.
LAST_TOPIC = {}


# ============================================================
# BASIC TEXT
# ============================================================

START_TEXT = f"""{BRAND}

The HZR AI says hello to you.

How can I help you today?

Type help or کمک for assistance.

{FOOTER}"""


HELP_TEXT = f"""{BRAND}

راهنمای HZR AI

می‌توانی تقریباً درباره هر موضوع عمومی سؤال بپرسی.

نمونه‌ها:

• مسی
• درباره مسی بگو
• لیونل مسی کیست؟
• افغانستان
• پایتخت افغانستان چیست؟
• درباره بارسلونا بگو
• What is Messi?
• Who is Lionel Messi?
• Tell me about Afghanistan
• Where is Afghanistan?

همچنین می‌توانی سؤال‌های What / Who / Where / When / Why / How را بپرسی.

محاسبات ساده نیز پشتیبانی می‌شوند:

25 * 4
100 / 5 + 7

{FOOTER}"""


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def contains_persian(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))


def contains_cyrillic(text: str) -> bool:
    return bool(re.search(r"[\u0400-\u04FF]", text))


def contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4E00-\u9FFF]", text))


def contains_japanese(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u30FF]", text))


def contains_korean(text: str) -> bool:
    return bool(re.search(r"[\uAC00-\uD7AF]", text))


def detect_language(text: str) -> str:
    """
    Best-effort language detection from script.
    """
    if contains_persian(text):
        return "fa"

    if contains_cyrillic(text):
        return "ru"

    if contains_chinese(text):
        return "zh"

    if contains_japanese(text):
        return "ja"

    if contains_korean(text):
        return "ko"

    # Latin-script languages cannot always be detected reliably.
    # English is used as the safest fallback.
    return "en"


# ============================================================
# QUERY CLEANING
# ============================================================

def clean_query(text: str) -> str:
    text = text.strip()

    prefixes = [
        "درباره",
        "در مورد",
        "راجع به",
        "معلومات درباره",
        "معلومات در مورد",
        "برای من درباره",
        "برای من در مورد",
        "tell me about",
        "tell me everything about",
        "what is",
        "what's",
        "who is",
        "who's",
        "where is",
        "when was",
        "when is",
        "why is",
        "how is",
        "how was",
        "how old is",
        "information about",
        "info about",
        "about",
    ]

    lower = text.lower()

    for prefix in prefixes:
        if lower.startswith(prefix.lower() + " "):
            text = text[len(prefix):].strip()
            break

    text = re.sub(
        r"^(کیست|چیست|چیه|کیه|کجاست|چه زمانی|چه وقت)\s*[\؟?]?$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    text = re.sub(r"[؟?!]+$", "", text).strip()

    return text


# ============================================================
# SAFE CALCULATOR
# ============================================================

def calculate(expression: str):
    expr = expression.strip()

    if len(expr) > 100:
        return None

    if not re.fullmatch(r"[0-9+\-*/().%\s×÷]+", expr):
        return None

    expr = (
        expr.replace("×", "*")
        .replace("÷", "/")
        .replace("−", "-")
    )

    if not re.search(r"[+\-*/%]", expr):
        return None

    try:
        # Restricted arithmetic only.
        result = eval(expr, {"__builtins__": {}}, {})

        if isinstance(result, (int, float)):
            if abs(result) > 10**100:
                return None

            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 10)

            return result

    except Exception:
        return None

    return None


# ============================================================
# WIKIPEDIA
# ============================================================

async def wiki_request(language: str, params: dict):
    url = f"https://{language}.wikipedia.org/w/api.php"

    params = {
        **params,
        "format": "json",
        "formatversion": "2",
        "utf8": "1",
    }

    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None

                return await response.json()

    except Exception:
        return None


async def wiki_search(language: str, query: str, limit: int = 6):
    data = await wiki_request(
        language,
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "srprop": "snippet|titlesnippet",
        },
    )

    if not data:
        return []

    return data.get("query", {}).get("search", [])


async def wiki_page(language: str, title: str):
    data = await wiki_request(
        language,
        {
            "action": "query",
            "prop": "extracts|pageimages|langlinks|info",
            "explaintext": "1",
            "exsectionformat": "plain",
            "exchars": "15000",
            "piprop": "original",
            "inprop": "url",
            "lllang": "fa",
            "lllimit": "1",
            "titles": title,
        },
    )

    if not data:
        return None

    pages = data.get("query", {}).get("pages", [])

    if not pages:
        return None

    page = pages[0]

    if page.get("missing"):
        return None

    return page


async def get_best_wikipedia_result(query: str):
    """
    Search order:
    1. Persian
    2. User's detected language
    3. English
    4. Several additional languages
    """

    detected = detect_language(query)

    languages = []

    for lang in [
        "fa",
        detected,
        "en",
        "ps",
        "ar",
        "ur",
        "tr",
        "de",
        "fr",
        "es",
        "it",
        "pt",
        "ru",
        "hi",
        "id",
    ]:
        if lang not in languages:
            languages.append(lang)

    for language in languages:
        results = await wiki_search(language, query, limit=6)

        if results:
            return language, results

    return None, []


# ============================================================
# PERSIAN PAGE REDIRECT
# ============================================================

async def get_persian_version(original_language: str, page: dict):
    """
    If the original page has a Persian language link,
    use the Persian Wikipedia page.
    """

    if original_language == "fa":
        return page

    langlinks = page.get("langlinks", [])

    if not langlinks:
        return page

    persian_title = None

    for link in langlinks:
        if link.get("lang") == "fa":
            persian_title = link.get("title")
            break

    if not persian_title:
        return page

    persian_page = await wiki_page("fa", persian_title)

    if persian_page:
        return persian_page

    return page


# ============================================================
# SEARCH BUTTON STORAGE
# ============================================================

def make_result_id(chat_id: int, title: str) -> str:
    raw = f"{chat_id}:{title}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def store_result(chat_id: int, title: str):
    result_id = make_result_id(chat_id, title)

    SEARCH_RESULTS[result_id] = {
        "chat_id": chat_id,
        "title": title,
    }

    # Keep memory under control.
    if len(SEARCH_RESULTS) > 1000:
        oldest = next(iter(SEARCH_RESULTS))
        SEARCH_RESULTS.pop(oldest, None)

    return result_id


# ============================================================
# THINKING MESSAGE
# ============================================================

async def thinking_animation(message):
    frames = [
        "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂.",
        "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂..",
        "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂...",
    ]

    for frame in frames:
        try:
            await message.edit_text(frame)
            await asyncio.sleep(0.35)
        except Exception:
            break


# ============================================================
# FORMAT WIKIPEDIA ANSWER
# ============================================================

def clean_wiki_text(text: str) -> str:
    if not text:
        return ""

    text = text.strip()

    # Remove excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def split_text(text: str, max_length: int = 3900):
    """
    Telegram messages have a 4096-character limit.
    Keep a safety margin for formatting.
    """

    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""

    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= max_length:
            current += paragraph + "\n\n"
        else:
            if current.strip():
                chunks.append(current.strip())

            # Very long paragraph.
            while len(paragraph) > max_length:
                chunks.append(paragraph[:max_length])
                paragraph = paragraph[max_length:]

            current = paragraph + "\n\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks


def build_header(title: str) -> str:
    return f"{BRAND}\n\n📚 {title}\n\n"


# ============================================================
# SEARCH RESULT MESSAGE
# ============================================================

async def show_search_results(
    update: Update,
    results,
    language: str,
    query: str,
):
    message = update.effective_message
    chat_id = update.effective_chat.id

    buttons = []

    for result in results[:6]:
        title = result.get("title", "").strip()

        if not title:
            continue

        result_id = store_result(chat_id, title)

        buttons.append(
            [
                InlineKeyboardButton(
                    title[:60],
                    callback_data=f"wiki:{result_id}",
                )
            ]
        )

    text = (
        f"{BRAND}\n\n"
        f"نتایج جست‌وجو برای:\n"
        f"«{query}»\n\n"
        f"یک موضوع را انتخاب کن:"
    )

    text += f"\n\n{FOOTER}"

    keyboard = InlineKeyboardMarkup(buttons) if buttons else None

    await message.edit_text(
        text,
        reply_markup=keyboard,
    )


# ============================================================
# SEND WIKIPEDIA PAGE
# ============================================================

async def send_wikipedia_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    language: str,
    title: str,
    edit_message=None,
):
    chat_id = update.effective_chat.id

    page = await wiki_page(language, title)

    if not page:
        fallback_language = "en" if language != "en" else "fa"

        if fallback_language != language:
            page = await wiki_page(fallback_language, title)
            language = fallback_language

    if not page:
        text = (
            f"{BRAND}\n\n"
            f"اطلاعات قابل اعتماد برای «{title}» پیدا نشد.\n\n"
            f"موضوع دقیق‌تری را امتحان کن.\n\n"
            f"{FOOTER}"
        )

        if edit_message:
            await edit_message.edit_text(text)
        else:
            await context.bot.send_message(chat_id=chat_id, text=text)

        return

    # Prefer Persian when available.
    persian_page = await get_persian_version(language, page)

    if persian_page:
        page = persian_page

    real_title = page.get("title", title)
    extract = clean_wiki_text(page.get("extract", ""))

    if not extract:
        extract = "برای این موضوع متن کافی در ویکی‌پدیا پیدا نشد."

    LAST_TOPIC[chat_id] = real_title

    header = build_header(real_title)

    full_text = header + extract + f"\n\n{FOOTER}"

    chunks = split_text(full_text)

    # First chunk replaces the existing thinking/search message.
    if edit_message:
        await edit_message.edit_text(chunks[0])
        chunks = chunks[1:]

    for chunk in chunks:
        await context.bot.send_message(
            chat_id=chat_id,
            text=chunk,
        )

    # Wikipedia image if available.
    original = page.get("original")

    if original and original.get("source"):
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=original["source"],
            )
        except Exception:
            pass


# ============================================================
# /START
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(START_TEXT)


# ============================================================
# /HELP
# ============================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(HELP_TEXT)


# ============================================================
# GREETINGS
# ============================================================

GREETING_WORDS = {
    "hi",
    "hello",
    "hey",
    "hola",
    "bonjour",
    "hallo",
    "ciao",
    "привет",
    "سلام",
    "سلام!",
    "سلام؟",
    "درود",
    "هلو",
    "مرحبا",
    "أهلا",
    "اهلا",
    "olá",
    "olá!",
}


def is_greeting(text: str) -> bool:
    normalized = text.strip().lower()
    normalized = re.sub(r"[!?.؟،,]+$", "", normalized)
    return normalized in GREETING_WORDS


async def send_greeting(message):
    await message.reply_text(
        f"{BRAND}\n\n"
        f"سلام.\n"
        f"چطور می‌توانم کمک کنم؟\n\n"
        f"{FOOTER}"
    )


# ============================================================
# CALLBACK BUTTONS
# ============================================================

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    data = query.data or ""

    if not data.startswith("wiki:"):
        return

    result_id = data.split(":", 1)[1]

    result = SEARCH_RESULTS.get(result_id)

    if not result:
        await query.edit_message_text(
            f"{BRAND}\n\n"
            f"این نتیجه دیگر در حافظه موقت HZR موجود نیست.\n\n"
            f"لطفاً دوباره جست‌وجو کن.\n\n"
            f"{FOOTER}"
        )
        return

    title = result["title"]

    await query.edit_message_text(
        "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂..."
    )

    await send_wikipedia_page(
        update,
        context,
        "fa",
        title,
        edit_message=query.message,
    )


# ============================================================
# MAIN MESSAGE HANDLER
# ============================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    message = update.message
    text = message.text.strip()

    if not text:
        return

    # Help in Persian.
    if text.lower() in {
        "کمک",
        "help",
        "راهنما",
        "/کمک",
    }:
        await message.reply_text(HELP_TEXT)
        return

    # Greetings.
    if is_greeting(text):
        await send_greeting(message)
        return

    # Arithmetic.
    result = calculate(text)

    if result is not None:
        await message.reply_text(
            f"{BRAND}\n\n"
            f"نتیجه:\n"
            f"{result}\n\n"
            f"{FOOTER}"
        )
        return

    # Clean the user's question.
    query = clean_query(text)

    # If the user asks a follow-up such as:
    # "پایتخت آن چیست؟"
    # use the previous topic.
    followup_patterns = [
        "آن چیست",
        "آن کجاست",
        "پایتختش چیست",
        "پایتخت آن",
        "او کیست",
        "این چیست",
        "what is its",
        "what is his",
        "what is her",
        "where is it",
        "what is the capital",
    ]

    lower = text.lower()

    if any(pattern in lower for pattern in followup_patterns):
        previous = LAST_TOPIC.get(update.effective_chat.id)

        if previous:
            query = f"{previous} {query}"

    # One message only: thinking message will become result.
    thinking = await message.reply_text(
        "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂."
    )

    await thinking_animation(thinking)

    # Search Wikipedia.
    language, results = await get_best_wikipedia_result(query)

    if not results:
        await thinking.edit_text(
            f"{BRAND}\n\n"
            f"اطلاعات قابل اعتماد برای:\n"
            f"«{text}»\n\n"
            f"پیدا نشد.\n\n"
            f"موضوع دقیق‌تری را امتحان کن.\n\n"
            f"{FOOTER}"
        )
        return

    # Exact / strongest result.
    first_title = results[0].get("title", "")

    normalized_query = re.sub(
        r"[^\w\u0600-\u06FF]+",
        "",
        query.lower(),
    )

    normalized_title = re.sub(
        r"[^\w\u0600-\u06FF]+",
        "",
        first_title.lower(),
    )

    # If the first result clearly matches, directly show it.
    if (
        normalized_query
        and (
            normalized_query == normalized_title
            or normalized_query in normalized_title
            or normalized_title in normalized_query
        )
    ):
        await send_wikipedia_page(
            update,
            context,
            language,
            first_title,
            edit_message=thinking,
        )
        return

    # For queries like "مسی", Wikipedia normally returns Messi as
    # the strongest result. If the result is very strong, use it.
    if len(results) == 1:
        await send_wikipedia_page(
            update,
            context,
            language,
            first_title,
            edit_message=thinking,
        )
        return

    # Show suggestions in the SAME message.
    # No separate suggestion message is created.
    await show_search_results(
        update,
        results,
        language,
        text,
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    print("HZR ERROR:", context.error)


# ============================================================
# HEALTH / STATUS
# ============================================================

async def health(request):
    return web.json_response(
        {
            "success": True,
            "service": "HZR19 AI Telegram Bot",
            "status": "online",
        }
    )


async def status(request):
    return web.json_response(
        {
            "success": True,
            "service": "HZR19 AI Telegram Bot",
            "status": "online",
            "mode": "webhook",
            "search": "Wikipedia multilingual",
        }
    )


# ============================================================
# WEBHOOK SERVER
# ============================================================

async def telegram_webhook(request):
    try:
        data = await request.json()

        update = Update.de_json(
            data,
            request.app["telegram_bot"],
        )

        await request.app["telegram_app"].process_update(update)

        return web.json_response({"ok": True})

    except Exception as error:
        print("WEBHOOK ERROR:", error)
        return web.json_response(
            {"ok": False},
            status=500,
        )


# ============================================================
# START SERVER
# ============================================================

async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    telegram_app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_app.add_handler(
        CommandHandler("start", start_command)
    )

    telegram_app.add_handler(
        CommandHandler("help", help_command)
    )

    telegram_app.add_handler(
        CallbackQueryHandler(callback_handler)
    )

    telegram_app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler,
        )
    )

    telegram_app.add_error_handler(error_handler)

    await telegram_app.initialize()
    await telegram_app.start()

    bot = telegram_app.bot

    # Remove any old webhook and install the current Render webhook.
    await bot.delete_webhook(drop_pending_updates=False)

    await bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES,
    )

    print("====================================")
    print("        HZR19 AI TELEGRAM BOT")
    print("====================================")
    print(f"Webhook: {WEBHOOK_URL}")
    print(f"Port: {PORT}")
    print("Status: ONLINE")
    print("====================================")

    app = web.Application()

    app["telegram_app"] = telegram_app
    app["telegram_bot"] = bot

    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_get("/api/status", status)

    app.router.add_post(
        WEBHOOK_PATH,
        telegram_webhook,
    )

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT,
    )

    await site.start()

    try:
        while True:
            await asyncio.sleep(3600)

    finally:
        await runner.cleanup()

        try:
            await telegram_app.stop()
            await telegram_app.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
