import os
import re
import asyncio
from urllib.parse import quote

import requests
from aiohttp import web

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# HZR19 SMART INFORMATION TELEGRAM BOT
# NO EXTERNAL AI
# Wikipedia / MediaWiki + Local Intelligence
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")


# =========================================================
# HZR19 FOOTER
# =========================================================

FOOTER = """
━━━━━━━━━━━━━━━━━━━━
        𝕳𝖅𝕽𝟏⁹
      2010-206
━━━━━━━━━━━━━━━━━━━━
"""


# =========================================================
# HTTP SESSION
# =========================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": (
        "HZR19-Information-Bot/1.0 "
        "(Telegram bot; MediaWiki API client)"
    ),
    "Accept": "application/json",
})


# =========================================================
# LANGUAGE CONFIGURATION
# =========================================================

LANGUAGES = {
    "fa": {
        "name": "فارسی",
        "wiki": "https://fa.wikipedia.org/w/api.php",
        "rtl": True,
    },

    "ps": {
        "name": "پښتو",
        "wiki": "https://ps.wikipedia.org/w/api.php",
        "rtl": True,
    },

    "ar": {
        "name": "العربية",
        "wiki": "https://ar.wikipedia.org/w/api.php",
        "rtl": True,
    },

    "en": {
        "name": "English",
        "wiki": "https://en.wikipedia.org/w/api.php",
        "rtl": False,
    },
}


# =========================================================
# COMMON WORDS
# =========================================================

STOP_WORDS = {
    # Persian / Dari
    "درباره",
    "راجع",
    "درمورد",
    "در",
    "مورد",
    "بگو",
    "بگوید",
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
    "معرفی‌اش",
    "معرفی",
    "میخواهم",
    "می‌خواهم",
    "لطفا",
    "لطفاً",
    "میشه",
    "می‌شود",
    "کن",
    "کنید",

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
    "information",
    "explain",
    "describe",
    "where",
    "when",
    "how",
}


# =========================================================
# LOCAL KNOWLEDGE
# =========================================================

LOCAL_KNOWLEDGE = {

    "سلام": (
        "سلام. من HZR19 هستم.\n\n"
        "موضوع یا سؤال خود را بفرستید. "
        "می‌توانید فقط نام یک موضوع را بنویسید، "
        "مثلاً «افغانستان»، «مسی»، «هوش مصنوعی» یا «تاریخ»."
    ),

    "hello": (
        "Hello. I am HZR19.\n\n"
        "Send me a topic or question and I will search "
        "my available information sources."
    ),

    "hi": (
        "Hello. I am HZR19.\n\n"
        "Send me a topic or question."
    ),

    "help": (
        "می‌توانید یک موضوع یا سؤال بفرستید.\n\n"
        "نمونه:\n"
        "• افغانستان\n"
        "• درباره هوش مصنوعی بگو\n"
        "• مسی کیست؟\n"
        "• پایتخت افغانستان چیست؟\n"
        "• تاریخ چیست؟"
    ),

    "کمک": (
        "می‌توانید یک موضوع یا سؤال بفرستید.\n\n"
        "نمونه:\n"
        "• افغانستان\n"
        "• درباره هوش مصنوعی بگو\n"
        "• مسی کیست؟\n"
        "• پایتخت افغانستان چیست؟"
    ),

    "تشکر": "خواهش می‌کنم.",
    "ممنون": "خواهش می‌کنم.",
    "thanks": "You're welcome.",
    "thank you": "You're welcome.",
}


# =========================================================
# TEXT UTILITIES
# =========================================================

def normalize_text(text: str) -> str:
    """
    Normalize Persian/Arabic/English text.
    """

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

    # Remove excessive spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def detect_language(text: str) -> str:
    """
    Basic local language detector.
    No AI is used.
    """

    text = normalize_text(text)

    if re.search(r"[\u0600-\u06FF]", text):

        # Pashto-specific characters
        pashto_chars = "ټځڅډړږښګڼېۍ"
        if any(char in text for char in pashto_chars):
            return "ps"

        # Arabic-specific letters
        arabic_chars = "ثذضظصط"
        if any(char in text for char in arabic_chars):
            return "ar"

        # Default Arabic-script language = Persian/Dari
        return "fa"

    return "en"


def clean_query(text: str) -> str:
    """
    Remove conversational filler while preserving the main topic.
    """

    text = normalize_text(text)

    # Remove question marks and common punctuation
    text = re.sub(r"[؟?!.,،؛:;]+", " ", text)

    words = text.split()

    cleaned = []

    for word in words:

        lower = word.lower()

        if lower in STOP_WORDS:
            continue

        if word in STOP_WORDS:
            continue

        cleaned.append(word)

    result = " ".join(cleaned).strip()

    # If everything was removed, use original text
    if not result:
        result = text

    return result


def shorten_text(text: str, max_chars: int = 3000) -> str:
    """
    Local text shortening.
    Does not use AI.
    """

    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_chars:
        return text

    # Prefer ending at a sentence
    portion = text[:max_chars]

    sentence_positions = [
        portion.rfind("۔"),
        portion.rfind("."),
        portion.rfind("!"),
        portion.rfind("؟"),
        portion.rfind("?"),
    ]

    best = max(sentence_positions)

    if best > int(max_chars * 0.55):
        return portion[:best + 1].strip()

    return portion.rstrip() + "…"


# =========================================================
# LOCAL INTELLIGENCE
# =========================================================

def local_response(text: str):
    """
    Very small internal knowledge layer.
    """

    normalized = normalize_text(text).lower()

    if normalized in LOCAL_KNOWLEDGE:
        return LOCAL_KNOWLEDGE[normalized]

    return None


def classify_question(text: str) -> str:
    """
    Determine the type of question using rules.
    """

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
    ]):
        return "who"

    if any(x in t for x in [
        "کجاست",
        "کجا است",
        "where is",
        "where was",
        "أين",
        "اين",
    ]):
        return "where"

    if any(x in t for x in [
        "چه زمانی",
        "کی",
        "چه وقت",
        "when",
        "متى",
    ]):
        return "when"

    if any(x in t for x in [
        "چگونه",
        "چطور",
        "how",
        "كيف",
    ]):
        return "how"

    if any(x in t for x in [
        "چرا",
        "why",
        "لماذا",
    ]):
        return "why"

    return "topic"


# =========================================================
# WIKIPEDIA SEARCH
# =========================================================

def wikipedia_search(query: str, lang: str, limit: int = 5):
    """
    Search Wikipedia using MediaWiki API.
    """

    config = LANGUAGES[lang]

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
        "utf8": 1,
    }

    try:
        response = SESSION.get(
            config["wiki"],
            params=params,
            timeout=12,
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("query", {}).get("search", [])

        return results

    except Exception as error:

        print(
            f"WIKIPEDIA SEARCH ERROR [{lang}]:",
            error
        )

        return []


# =========================================================
# WIKIPEDIA PAGE DATA
# =========================================================

def wikipedia_page(title: str, lang: str):
    """
    Get article extract + thumbnail + page URL.
    """

    config = LANGUAGES[lang]

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": title,

        "prop": "extracts|pageimages|info",

        "exintro": 1,
        "explaintext": 1,
        "exchars": 5000,

        "piprop": "thumbnail|original",
        "pithumbsize": 900,

        "inprop": "url",

        "redirects": 1,
    }

    try:

        response = SESSION.get(
            config["wiki"],
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        pages = data.get("query", {}).get("pages", [])

        if not pages:
            return None

        page = pages[0]

        if page.get("missing"):
            return None

        return {
            "title": page.get("title", title),
            "extract": page.get("extract", "").strip(),
            "thumbnail": (
                page.get("thumbnail", {}).get("source")
            ),
            "original": (
                page.get("original", {}).get("source")
            ),
            "url": page.get(
                "fullurl",
                f"https://{lang}.wikipedia.org/wiki/"
                f"{quote(page.get('title', title).replace(' ', '_'))}"
            ),
            "lang": lang,
        }

    except Exception as error:

        print(
            f"WIKIPEDIA PAGE ERROR [{lang}]:",
            error
        )

        return None


# =========================================================
# SMART SEARCH
# =========================================================

def find_information(user_text: str):
    """
    Main non-AI information engine.

    Strategy:
    1. Detect language.
    2. Extract topic.
    3. Search selected Wikipedia.
    4. Try other languages if necessary.
    """

    language = detect_language(user_text)

    cleaned = clean_query(user_text)

    if not cleaned:
        cleaned = user_text

    # First search user's language
    language_order = [language]

    # Then fallback languages
    for lang in ["fa", "ps", "ar", "en"]:
        if lang not in language_order:
            language_order.append(lang)

    for lang in language_order:

        results = wikipedia_search(
            cleaned,
            lang,
            limit=5
        )

        if not results:
            continue

        # Try first few search results
        for result in results[:3]:

            title = result.get("title")

            if not title:
                continue

            page = wikipedia_page(
                title,
                lang
            )

            if not page:
                continue

            extract = page.get("extract", "")

            if not extract:
                continue

            return page

    return None


# =========================================================
# ANSWER BUILDER
# =========================================================

def build_answer(user_text: str, page: dict) -> str:
    """
    Convert retrieved information into a clean HZR19 answer.
    """

    language = page["lang"]
    title = page["title"]
    extract = page["extract"]

    question_type = classify_question(user_text)

    extract = shorten_text(
        extract,
        max_chars=3000
    )

    if language == "en":

        if question_type == "who":
            intro = f"Here is information about {title}:"

        elif question_type == "where":
            intro = f"Information related to {title}:"

        elif question_type == "what":
            intro = f"{title}:"

        else:
            intro = f"Information about {title}:"

    elif language == "ar":

        if question_type == "who":
            intro = f"إليك معلومات عن {title}:"

        elif question_type == "what":
            intro = f"{title}:"

        else:
            intro = f"معلومات عن {title}:"

    elif language == "ps":

        if question_type == "who":
            intro = f"د {title} په اړه معلومات:"

        elif question_type == "what":
            intro = f"{title}:"

        else:
            intro = f"د {title} په اړه معلومات:"

    else:

        if question_type == "who":
            intro = f"درباره «{title}» اطلاعات زیر را پیدا کردم:"

        elif question_type == "what":
            intro = f"«{title}» چیست؟"

        else:
            intro = f"درباره «{title}» اطلاعات زیر را پیدا کردم:"

    answer = (
        f"{intro}\n\n"
        f"{extract}\n\n"
        f"منبع: Wikipedia\n"
        f"{page['url']}"
    )

    return answer


# =========================================================
# THINKING ANIMATION
# =========================================================

async def thinking_animation(message):

    dots = 1

    try:

        while True:

            text = (
                "HZR IS THINKING"
                + "." * dots
            )

            try:
                await message.edit_text(text)
            except Exception:
                pass

            dots += 1

            if dots > 3:
                dots = 1

            await asyncio.sleep(0.7)

    except asyncio.CancelledError:
        pass

    except Exception:
        pass


# =========================================================
# TEXT SPLITTER
# =========================================================

def split_message(text: str, limit: int = 3900):

    if len(text) <= limit:
        return [text]

    parts = []

    while text:

        if len(text) <= limit:
            parts.append(text)
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
# SEND ANSWER
# =========================================================

async def send_answer(
    update: Update,
    answer: str,
    page=None,
):

    # Remove footer temporarily to ensure
    # each final message has it correctly.
    final_text = answer + FOOTER

    parts = split_message(
        final_text
    )

    # Send image first if available
    if page:

        image_url = (
            page.get("thumbnail")
            or page.get("original")
        )

        if image_url:

            try:

                caption = (
                    f"تصویر مرتبط با: "
                    f"{page['title']}"
                )

                await update.message.reply_photo(
                    photo=image_url,
                    caption=caption
                )

            except Exception as error:

                print(
                    "IMAGE SEND ERROR:",
                    error
                )

    for part in parts:

        await update.message.reply_text(
            part,
            disable_web_page_preview=False
        )


# =========================================================
# START COMMAND
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = (
        "سلام.\n\n"
        "من 𝕳𝖅𝕽𝟏⁹ هستم.\n\n"
        "من برای پاسخ‌گویی از موتور هوش مصنوعی خارجی "
        "استفاده نمی‌کنم. سیستم اطلاعاتی HZR19 با "
        "جست‌وجو، تحلیل متن و منابع اطلاعاتی کار می‌کند.\n\n"
        "می‌توانید فقط نام یک موضوع را بفرستید:\n\n"
        "• افغانستان\n"
        "• هوش مصنوعی\n"
        "• لیونل مسی\n"
        "• تاریخ\n\n"
        "یا سؤال کامل بنویسید:\n\n"
        "«درباره افغانستان بگو»\n"
        "«مسی کیست؟»\n"
        "«هوش مصنوعی چیست؟»"
        + FOOTER
    )

    await update.message.reply_text(
        message
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

    user_text = update.message.text.strip()

    if not user_text:
        return

    print(
        "USER REQUEST:",
        user_text
    )

    # -----------------------------------------
    # Local response
    # -----------------------------------------

    local = local_response(
        user_text
    )

    if local:

        await update.message.reply_text(
            local + FOOTER
        )

        return

    # -----------------------------------------
    # Thinking message
    # -----------------------------------------

    thinking_message = (
        await update.message.reply_text(
            "HZR IS THINKING."
        )
    )

    animation_task = asyncio.create_task(
        thinking_animation(
            thinking_message
        )
    )

    try:

        # Run blocking Wikipedia requests
        # outside the Telegram event loop.
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

        # Delete thinking message
        try:
            await thinking_message.delete()
        except Exception:
            pass

        # -----------------------------------------
        # Information found
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
        # Nothing found
        # -----------------------------------------

        language = detect_language(
            user_text
        )

        if language == "en":

            answer = (
                "I could not find a reliable Wikipedia "
                "article matching your request.\n\n"
                "Try writing the topic more clearly."
            )

        elif language == "ar":

            answer = (
                "لم أجد مقالة موثوقة مطابقة لطلبك "
                "في المصادر المتاحة.\n\n"
                "حاول كتابة الموضوع بشكل أوضح."
            )

        elif language == "ps":

            answer = (
                "ستاسې د غوښتنې لپاره مې مناسبه "
                "ویکيپیډیا مقاله پیدا نه کړه.\n\n"
                "موضوع لږ روښانه ولیکئ."
            )

        else:

            answer = (
                "برای این درخواست اطلاعات مناسبی "
                "در منابع فعلی پیدا نکردم.\n\n"
                "لطفاً موضوع را کمی واضح‌تر بنویسید."
            )

        await update.message.reply_text(
            answer + FOOTER
        )

    except Exception as error:

        print(
            "MESSAGE ERROR:",
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
            "در پردازش درخواست خطایی رخ داد."
            + FOOTER
        )


# =========================================================
# RENDER HEALTH CHECK
# =========================================================

async def health(request):

    return web.Response(
        text=(
            "HZR19 AI Telegram Bot is online.\n"
            "External AI: OFF\n"
            "Information Engine: Wikipedia/MediaWiki"
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
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
