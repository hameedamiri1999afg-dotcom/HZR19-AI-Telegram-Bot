import os
import re
import asyncio
import html
from urllib.parse import quote

import requests
from aiohttp import web

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# HZR19 SMART INFORMATION ENGINE
# NO EXTERNAL AI
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")


# =========================================================
# BRAND
# =========================================================

HZR_TAG = "@m19_goat"


# =========================================================
# HTTP SESSION
# =========================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": (
        "HZR19-Information-Bot/2.0 "
        "(Telegram bot; MediaWiki API client)"
    ),
    "Accept": "application/json",
})


# =========================================================
# LANGUAGES
# =========================================================

LANGUAGES = {
    "fa": {
        "name": "فارسی",
        "wiki": "https://fa.wikipedia.org/w/api.php",
    },

    "ps": {
        "name": "پښتو",
        "wiki": "https://ps.wikipedia.org/w/api.php",
    },

    "ar": {
        "name": "العربية",
        "wiki": "https://ar.wikipedia.org/w/api.php",
    },

    "en": {
        "name": "English",
        "wiki": "https://en.wikipedia.org/w/api.php",
    },
}


# =========================================================
# LOCAL KNOWLEDGE
# =========================================================

LOCAL_KNOWLEDGE = {

    "سلام": (
        "سلام.\n\n"
        "من HZR19 هستم.\n"
        "موضوع یا سؤال خود را بفرستید."
    ),

    "hello": (
        "Hello.\n\n"
        "I am HZR19.\n"
        "Send me a topic or question."
    ),

    "hi": (
        "Hello.\n\n"
        "Send me a topic or question."
    ),

    "تشکر": "خواهش می‌کنم.",
    "ممنون": "خواهش می‌کنم.",
    "thanks": "You're welcome.",
    "thank you": "You're welcome.",
}


# =========================================================
# STOP WORDS
# =========================================================

STOP_WORDS = {
    # Persian / Dari
    "درباره",
    "راجع",
    "راجب",
    "درمورد",
    "در",
    "مورد",
    "بگو",
    "بگوید",
    "بگویم",
    "برایم",
    "من",
    "یک",
    "چیست",
    "کیست",
    "است",
    "هست",
    "هستش",
    "را",
    "رو",
    "از",
    "به",
    "و",
    "یا",
    "که",
    "چه",
    "چگونه",
    "چطور",
    "کجا",
    "کی",
    "اطلاعات",
    "اطلاعاتی",
    "توضیح",
    "توضیحی",
    "معرفی",
    "میخواهم",
    "می‌خواهم",
    "لطفا",
    "لطفاً",
    "میشه",
    "می‌شود",
    "کن",
    "کنید",
    "درباره‌اش",
    "راجع‌به",

    # Pashto
    "په",
    "اړه",
    "کې",
    "څه",
    "څوک",
    "دی",
    "ده",
    "راکړه",
    "معلومات",
    "ووایه",
    "وایه",

    # Arabic
    "عن",
    "حول",
    "ما",
    "هو",
    "هي",
    "من",
    "في",
    "على",
    "الى",
    "إلى",
    "و",
    "أخبرني",
    "اعطني",
    "أعطني",
    "معلومات",
    "ماذا",
    "كيف",
    "أين",
    "من",
    "هو",
    "هي",

    # English
    "about",
    "tell",
    "me",
    "what",
    "is",
    "who",
    "are",
    "the",
    "a",
    "an",
    "of",
    "in",
    "on",
    "to",
    "for",
    "and",
    "or",
    "please",
    "give",
    "information",
    "explain",
    "describe",
    "where",
    "when",
    "how",
    "does",
    "do",
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_text(text: str) -> str:

    text = text.strip()

    replacements = {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "ٱ": "ا",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# LANGUAGE DETECTION
# =========================================================

def detect_language(text: str) -> str:

    text = normalize_text(text)

    # Pashto characters
    pashto_chars = "ټځڅډړږښګڼېۍ"

    if any(char in text for char in pashto_chars):
        return "ps"

    # Arabic characters
    arabic_chars = "ثذضظصط"

    if any(char in text for char in arabic_chars):
        return "ar"

    # Persian characters
    if re.search(r"[گچپژ]", text):
        return "fa"

    # Arabic-script default
    if re.search(r"[\u0600-\u06FF]", text):
        return "fa"

    return "en"


# =========================================================
# QUERY EXTRACTION
# =========================================================

def clean_query(text: str) -> str:

    text = normalize_text(text)

    text = re.sub(
        r"[؟?!.,،؛:;()\[\]{}]+",
        " ",
        text
    )

    words = text.split()

    result = []

    for word in words:

        if word in STOP_WORDS:
            continue

        if word.lower() in STOP_WORDS:
            continue

        result.append(word)

    cleaned = " ".join(result).strip()

    if not cleaned:
        cleaned = text

    return cleaned


# =========================================================
# QUESTION TYPE
# =========================================================

def classify_question(text: str) -> str:

    t = normalize_text(text).lower()

    if any(x in t for x in [
        "چیست",
        "چی هست",
        "چه است",
        "what is",
        "what's",
        "ما هو",
        "ما هي",
    ]):
        return "what"

    if any(x in t for x in [
        "کیست",
        "کی بود",
        "who is",
        "who was",
        "من هو",
        "من هي",
        "څوک دی",
        "څوک ده",
    ]):
        return "who"

    if any(x in t for x in [
        "کجاست",
        "کجا است",
        "where is",
        "where was",
        "أين",
        "اين",
        "چیرته",
        "چرته",
    ]):
        return "where"

    if any(x in t for x in [
        "چه زمانی",
        "چه وقت",
        "when",
        "متى",
        "کله",
    ]):
        return "when"

    if any(x in t for x in [
        "چگونه",
        "چطور",
        "how",
        "كيف",
        "څنګه",
    ]):
        return "how"

    if any(x in t for x in [
        "چرا",
        "why",
        "لماذا",
        "ولې",
    ]):
        return "why"

    return "topic"


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_wikipedia_text(text: str) -> str:

    text = re.sub(
        r"\[[0-9]+\]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def smart_shorten(
    text: str,
    max_chars: int = 3500
) -> str:

    text = clean_wikipedia_text(text)

    if len(text) <= max_chars:
        return text

    cut = text[:max_chars]

    positions = [
        cut.rfind("۔"),
        cut.rfind("."),
        cut.rfind("!"),
        cut.rfind("؟"),
        cut.rfind("?"),
    ]

    best = max(positions)

    if best >= int(max_chars * 0.60):
        return cut[:best + 1].strip()

    return cut.rstrip() + "…"


# =========================================================
# WIKIPEDIA SEARCH
# =========================================================

def wikipedia_search(
    query: str,
    lang: str,
    limit: int = 8
):

    config = LANGUAGES[lang]

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "srprop": "snippet",
        "format": "json",
        "utf8": 1,
    }

    try:

        response = SESSION.get(
            config["wiki"],
            params=params,
            timeout=15
        )

        response.raise_for_status()

        return (
            response
            .json()
            .get("query", {})
            .get("search", [])
        )

    except Exception as error:

        print(
            f"SEARCH ERROR [{lang}]:",
            error
        )

        return []


# =========================================================
# WIKIPEDIA PAGE
# =========================================================

def wikipedia_page(
    title: str,
    lang: str
):

    config = LANGUAGES[lang]

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": title,

        "prop": "extracts|pageimages|info",

        "exintro": 1,
        "explaintext": 1,
        "exchars": 7000,

        "piprop": "thumbnail|original",
        "pithumbsize": 1000,

        "inprop": "url",

        "redirects": 1,
    }

    try:

        response = SESSION.get(
            config["wiki"],
            params=params,
            timeout=15
        )

        response.raise_for_status()

        pages = (
            response
            .json()
            .get("query", {})
            .get("pages", [])
        )

        if not pages:
            return None

        page = pages[0]

        if page.get("missing"):
            return None

        return {
            "title": page.get(
                "title",
                title
            ),

            "extract": page.get(
                "extract",
                ""
            ).strip(),

            "thumbnail": (
                page.get(
                    "thumbnail",
                    {}
                ).get("source")
            ),

            "original": (
                page.get(
                    "original",
                    {}
                ).get("source")
            ),

            "url": page.get(
                "fullurl",
                ""
            ),

            "lang": lang,
        }

    except Exception as error:

        print(
            f"PAGE ERROR [{lang}]:",
            error
        )

        return None


# =========================================================
# SEARCH ENGINE
# =========================================================

def find_information(
    user_text: str
):

    language = detect_language(
        user_text
    )

    query = clean_query(
        user_text
    )

    if not query:
        query = user_text

    # User language first
    languages = [language]

    # Then international fallbacks
    for lang in [
        "fa",
        "ps",
        "ar",
        "en"
    ]:

        if lang not in languages:
            languages.append(lang)

    for lang in languages:

        results = wikipedia_search(
            query,
            lang,
            limit=8
        )

        if not results:
            continue

        # Check several results.
        for result in results[:5]:

            title = result.get(
                "title"
            )

            if not title:
                continue

            page = wikipedia_page(
                title,
                lang
            )

            if not page:
                continue

            if not page.get(
                "extract"
            ):
                continue

            return page

    return None


# =========================================================
# SMART ANSWER FORMATTER
# =========================================================

def build_answer(
    user_text: str,
    page: dict
):

    title = page["title"]

    extract = smart_shorten(
        page["extract"],
        3500
    )

    question_type = classify_question(
        user_text
    )

    lang = page["lang"]

    # -----------------------------------------
    # Persian / Dari
    # -----------------------------------------

    if lang == "fa":

        if question_type == "what":

            return (
                f"**{title}**\n\n"
                f"{extract}"
            )

        if question_type == "who":

            return (
                f"**{title}**\n\n"
                f"{extract}"
            )

        return (
            f"**{title}**\n\n"
            f"{extract}"
        )

    # -----------------------------------------
    # Pashto
    # -----------------------------------------

    if lang == "ps":

        return (
            f"**{title}**\n\n"
            f"{extract}"
        )

    # -----------------------------------------
    # Arabic
    # -----------------------------------------

    if lang == "ar":

        return (
            f"**{title}**\n\n"
            f"{extract}"
        )

    # -----------------------------------------
    # English
    # -----------------------------------------

    return (
        f"**{title}**\n\n"
        f"{extract}"
    )


# =========================================================
# FINAL HZR FORMAT
# =========================================================

def final_format(text: str) -> str:

    return (
        text.strip()
        + "\n\n"
        + HZR_TAG
    )


# =========================================================
# THINKING ANIMATION
# =========================================================

THINKING_FRAMES = [
    "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂",
    "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂 ·",
    "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂 ··",
]


async def thinking_animation(
    message
):

    index = 0

    try:

        while True:

            try:

                await message.edit_text(
                    THINKING_FRAMES[index]
                )

            except Exception:
                pass

            index += 1

            if index >= len(
                THINKING_FRAMES
            ):
                index = 0

            await asyncio.sleep(
                0.65
            )

    except asyncio.CancelledError:
        pass

    except Exception:
        pass


# =========================================================
# TELEGRAM MESSAGE SPLITTER
# =========================================================

def split_message(
    text: str,
    limit: int = 3900
):

    if len(text) <= limit:
        return [text]

    parts = []

    while text:

        if len(text) <= limit:

            parts.append(
                text.strip()
            )

            break

        cut = text.rfind(
            "\n",
            0,
            limit
        )

        if cut < 1000:

            cut = text.rfind(
                " ",
                0,
                limit
            )

        if cut < 1000:
            cut = limit

        parts.append(
            text[:cut].strip()
        )

        text = text[cut:].strip()

    return parts


# =========================================================
# SEND IMAGE
# =========================================================

async def send_image(
    message,
    page
):

    image_url = (
        page.get("thumbnail")
        or page.get("original")
    )

    if not image_url:
        return

    try:

        await message.reply_photo(
            photo=image_url
        )

    except Exception as error:

        print(
            "IMAGE ERROR:",
            error
        )


# =========================================================
# SEND ANSWER
# =========================================================

async def send_answer(
    update: Update,
    answer: str,
    page=None
):

    # Image
    if page:

        await send_image(
            update.message,
            page
        )

    # Final answer
    final_answer = final_format(
        answer
    )

    parts = split_message(
        final_answer
    )

    for part in parts:

        await update.message.reply_text(
            part,
            parse_mode=ParseMode.MARKDOWN
        )


# =========================================================
# START
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "سلام.\n\n"
        "من 𝙃𝙕𝙍𝟏⁹ هستم.\n\n"
        "موضوع یا سؤال خود را بفرستید.\n\n"
        "مثلاً:\n"
        "افغانستان\n"
        "درباره افغانستان بگو\n"
        "هوش مصنوعی چیست؟\n"
        "مسی کیست؟"
    )

    await update.message.reply_text(
        final_format(text)
    )


# =========================================================
# MAIN MESSAGE HANDLER
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    user_text = (
        update.message.text.strip()
    )

    if not user_text:
        return

    print(
        "USER:",
        user_text
    )

    # -----------------------------------------
    # Local responses
    # -----------------------------------------

    normalized = normalize_text(
        user_text
    ).lower()

    if normalized in LOCAL_KNOWLEDGE:

        await update.message.reply_text(
            final_format(
                LOCAL_KNOWLEDGE[
                    normalized
                ]
            )
        )

        return

    # -----------------------------------------
    # Thinking
    # -----------------------------------------

    thinking_message = (
        await update.message.reply_text(
            THINKING_FRAMES[0]
        )
    )

    animation_task = asyncio.create_task(
        thinking_animation(
            thinking_message
        )
    )

    try:

        # Search without blocking Telegram
        page = await asyncio.to_thread(
            find_information,
            user_text
        )

        # Stop animation
        animation_task.cancel()

        try:
            await animation_task
        except asyncio.CancelledError:
            pass

        # Remove thinking message
        try:
            await thinking_message.delete()
        except Exception:
            pass

        # -----------------------------------------
        # Result
        # -----------------------------------------

        if page:

            answer = build_answer(
                user_text,
                page
            )

            await send_answer(
                update,
                answer,
                page
            )

            return

        # -----------------------------------------
        # No result
        # -----------------------------------------

        lang = detect_language(
            user_text
        )

        if lang == "en":

            answer = (
                "I could not find enough reliable "
                "information for this request."
            )

        elif lang == "ar":

            answer = (
                "لم أتمكن من العثور على معلومات "
                "موثوقة كافية لهذا الطلب."
            )

        elif lang == "ps":

            answer = (
                "د دې غوښتنې لپاره مې کافي باوري "
                "معلومات پیدا نه کړل."
            )

        else:

            answer = (
                "برای این درخواست اطلاعات کافی "
                "و قابل‌اعتمادی پیدا نکردم."
            )

        await update.message.reply_text(
            final_format(answer)
        )

    except Exception as error:

        print(
            "HANDLER ERROR:",
            error
        )

        animation_task.cancel()

        try:
            await animation_task
        except Exception:
            pass

        try:
            await thinking_message.delete()
        except Exception:
            pass

        await update.message.reply_text(
            final_format(
                "در پردازش درخواست خطایی رخ داد."
            )
        )


# =========================================================
# RENDER HEALTH
# =========================================================

async def health(
    request
):

    return web.Response(
        text=(
            "HZR19 Smart Information Bot\n"
            "Status: ONLINE\n"
            "External AI: OFF\n"
            "Engine: HZR19 Local Intelligence"
        )
    )


async def start_web_server():

    app = web.Application()

    app.router.add_get(
        "/",
        health
    )

    app.router.add_get(
        "/health",
        health
    )

    runner = web.AppRunner(
        app
    )

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    print(
        f"HZR19 web server running on port {PORT}"
    )


# =========================================================
# MAIN
# =========================================================

async def main():

    await start_web_server()

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print(
        "HZR19 Telegram Bot starting..."
    )

    await application.initialize()

    await application.start()

    await application.updater.start_polling()

    print(
        "HZR19 Telegram Bot is running."
    )

    try:

        while True:
            await asyncio.sleep(3600)

    except asyncio.CancelledError:
        pass

    finally:

        await application.updater.stop()

        await application.stop()

        await application.shutdown()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
