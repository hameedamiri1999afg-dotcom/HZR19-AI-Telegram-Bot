import os
import re
import ast
import operator
import hashlib
import asyncio
from collections import defaultdict, deque

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
).rstrip("/")

WEBHOOK_PATH = "/telegram/webhook"

HZR_TAG = "@m19_goat"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing.")

WEBHOOK_SECRET = hashlib.sha256(
    BOT_TOKEN.encode("utf-8")
).hexdigest()[:32]

APPLICATION = None
HTTP_SESSION = None


# ============================================================
# MEMORY
# ============================================================

USER_MEMORY = defaultdict(lambda: deque(maxlen=8))


def remember(user_id, topic):
    if topic:
        USER_MEMORY[user_id].append(topic)


def get_last_topic(user_id):
    if USER_MEMORY[user_id]:
        return USER_MEMORY[user_id][-1]
    return None


# ============================================================
# TEXT
# ============================================================

def normalize_text(text):
    if not text:
        return ""

    text = text.strip()

    replacements = {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return re.sub(r"\s+", " ", text).strip()


def detect_language(text):
    text = normalize_text(text)

    if re.search(r"[\u0600-\u06ff]", text):
        return "fa"

    if re.search(r"[\u0400-\u04ff]", text):
        return "ru"

    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"

    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"

    return "en"


# ============================================================
# START
# ============================================================

START_TEXT = f"""𝕳𝖅𝕽𝟏⁹

The HZR AI says hello to you.

How can I help you today?

Type help or کمک for assistance.

{HZR_TAG}"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT)


# ============================================================
# HELP
# ============================================================

HELP_EN = f"""𝕳𝖅𝕽𝟏⁹

HZR AI can search for information and help you explore different topics.

You can ask questions such as:

What is Afghanistan?
Tell me about Barcelona
Who is Messi?
Where is Kabul?
When did World War II begin?
Why is the sky blue?
Calculate 25 × 4

You can also send only a topic:

Afghanistan
Barcelona
Lionel Messi
Python
Space

When several results are available, HZR will show search suggestions.

Commands:

/start
/help
/status

You can also type:

کمک

{HZR_TAG}"""


HELP_FA = f"""𝕳𝖅𝕽𝟏⁹

HZR AI می‌تواند درباره موضوعات مختلف اطلاعات پیدا کند و به پرسش‌های شما پاسخ دهد.

می‌توانی سؤال‌هایی مثل این بپرسی:

افغانستان چیست؟
درباره افغانستان بگو
پایتخت افغانستان چیست؟
مسی کیست؟
بارسلونا کجاست؟
جنگ جهانی دوم چه زمانی آغاز شد؟
چرا آسمان آبی است؟
25 × 4

همچنین می‌توانی فقط نام موضوع را بفرستی:

افغانستان
بارسلونا
لیونل مسی
پایتون
فضا

اگر چند نتیجه وجود داشته باشد، HZR پیشنهادهای جستجو را نشان می‌دهد.

دستورها:

/start
/help
/status

برای راهنما همچنین می‌توانی بنویسی:

کمک

{HZR_TAG}"""


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    language = detect_language(update.message.text or "")

    if language == "fa":
        await update.message.reply_text(HELP_FA)
    else:
        await update.message.reply_text(HELP_EN)


# ============================================================
# STATUS
# ============================================================

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"""𝕳𝖅𝕽𝟏⁹

Status: Online
Mode: Webhook
Search: Wikipedia
Memory: Active

{HZR_TAG}"""
    )


# ============================================================
# GREETINGS
# ============================================================

GREETINGS = {
    "hi": "Hello. How can I help you today?",
    "hello": "Hello. How can I help you today?",
    "hey": "Hey. What would you like to know?",
    "سلام": "سلام. HZR آماده است. چه کمکی می‌توانم بکنم؟",
    "درود": "درود. چه چیزی می‌خواهی بدانید؟",
    "مرحبا": "مرحباً. كيف يمكنني مساعدتك؟",
    "اهلا": "أهلاً. كيف يمكنني مساعدتك؟",
    "hola": "Hola. ¿Cómo puedo ayudarte?",
    "bonjour": "Bonjour. Comment puis-je vous aider ?",
    "hallo": "Hallo. Wie kann ich dir helfen?",
    "ciao": "Ciao. Come posso aiutarti?",
    "привет": "Привет. Чем я могу помочь?",
    "你好": "你好。有什么可以帮助你的吗？",
    "こんにちは": "こんにちは。何をお手伝いできますか？",
}


def get_greeting(text):
    value = normalize_text(text).casefold()
    return GREETINGS.get(value)


# ============================================================
# CALCULATOR
# ============================================================

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def calculate_node(node):

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            if abs(node.value) > 10**12:
                raise ValueError
            return node.value
        raise ValueError

    if isinstance(node, ast.UnaryOp):
        operation = OPERATORS.get(type(node.op))

        if not operation:
            raise ValueError

        return operation(calculate_node(node.operand))

    if isinstance(node, ast.BinOp):
        operation = OPERATORS.get(type(node.op))

        if not operation:
            raise ValueError

        left = calculate_node(node.left)
        right = calculate_node(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError

        result = operation(left, right)

        if abs(result) > 10**12:
            raise ValueError

        return result

    raise ValueError


def safe_calculate(expression):

    expression = expression.strip()

    expression = expression.replace("×", "*")
    expression = expression.replace("÷", "/")
    expression = expression.replace("−", "-")
    expression = expression.replace(",", "")

    if not re.fullmatch(
        r"[0-9+\-*/().%\s]+",
        expression
    ):
        return None

    try:
        tree = ast.parse(
            expression,
            mode="eval"
        )

        return calculate_node(tree.body)

    except Exception:
        return None


def looks_like_calculation(text):

    text = text.strip()

    if not re.fullmatch(
        r"[0-9+\-*/×÷−().%\s]+",
        text
    ):
        return False

    return (
        any(c.isdigit() for c in text)
        and any(
            c in text
            for c in "+-*/×÷−%"
        )
    )


def format_number(value):

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(round(value, 10))


# ============================================================
# HTTP SESSION
# ============================================================

async def get_session():

    global HTTP_SESSION

    if HTTP_SESSION is None:
        HTTP_SESSION = aiohttp.ClientSession(
            headers={
                "User-Agent": "HZR19-AI-Telegram-Bot/1.0"
            }
        )

    return HTTP_SESSION


# ============================================================
# WIKIPEDIA SEARCH
# ============================================================

async def wikipedia_search(query, language="en", limit=6):

    query = normalize_text(query)

    if not query:
        return []

    session = await get_session()

    url = f"https://{language}.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
        "utf8": 1,
    }

    try:

        async with session.get(
            url,
            params=params,
            timeout=aiohttp.ClientTimeout(total=12)
        ) as response:

            if response.status != 200:
                return []

            data = await response.json()

            results = []

            for item in data.get(
                "query",
                {}
            ).get(
                "search",
                []
            ):

                title = item.get(
                    "title",
                    ""
                ).strip()

                if title:
                    results.append(title)

            return results

    except Exception as error:

        print(
            "Wikipedia search error:",
            error
        )

        return []


# ============================================================
# WIKIPEDIA PAGE
# ============================================================

async def wikipedia_page(title, language="en"):

    session = await get_session()

    url = f"https://{language}.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "prop": "extracts|pageimages",
        "explaintext": 1,
        "exchars": 14000,
        "titles": title,
        "redirects": 1,
        "format": "json",
        "utf8": 1,
        "pithumbsize": 900,
    }

    try:

        async with session.get(
            url,
            params=params,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as response:

            if response.status != 200:
                return None

            data = await response.json()

            pages = data.get(
                "query",
                {}
            ).get(
                "pages",
                {}
            )

            for page in pages.values():

                if "missing" in page:
                    continue

                return {
                    "title": page.get(
                        "title",
                        title
                    ),
                    "extract": page.get(
                        "extract",
                        ""
                    ).strip(),
                    "image": page.get(
                        "thumbnail",
                        {}
                    ).get(
                        "source"
                    ),
                }

    except Exception as error:

        print(
            "Wikipedia page error:",
            error
        )

    return None


# ============================================================
# SUGGESTION BUTTONS
# ============================================================

def make_suggestion_keyboard(results):

    rows = []

    for title in results[:6]:

        # Telegram callback data has a size limit,
        # therefore keep the title short.
        safe_title = title[:180]

        rows.append([
            InlineKeyboardButton(
                f"🔎 {title}",
                callback_data=f"wiki:{safe_title}"
            )
        ])

    if not rows:
        return None

    return InlineKeyboardMarkup(rows)


# ============================================================
# SEARCH LANGUAGE
# ============================================================

async def search_in_best_language(
    query,
    language
):

    if language == "fa":

        results = await wikipedia_search(
            query,
            "fa",
            6
        )

        if results:
            return results, "fa"

        results = await wikipedia_search(
            query,
            "en",
            6
        )

        return results, "en"

    results = await wikipedia_search(
        query,
        "en",
        6
    )

    return results, "en"


# ============================================================
# QUERY CLEANING
# ============================================================

def clean_query(text):

    value = normalize_text(text)

    patterns = [
        r"^درباره\s+",
        r"^در مورد\s+",
        r"^what is\s+",
        r"^who is\s+",
        r"^where is\s+",
        r"^when is\s+",
        r"^tell me about\s+",
        r"^information about\s+",
        r"^info about\s+",
        r"^about\s+",
    ]

    for pattern in patterns:

        value = re.sub(
            pattern,
            "",
            value,
            flags=re.IGNORECASE
        )

    value = re.sub(
        r"(چیست|کیست|کجاست|چه است|چی میدانی|چه میدانی)\s*\??$",
        "",
        value,
        flags=re.IGNORECASE
    )

    return value.strip()


# ============================================================
# THINKING
# ============================================================

async def show_thinking(chat_id):

    message = await APPLICATION.bot.send_message(
        chat_id=chat_id,
        text="𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂."
    )

    frames = [
        "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂..",
        "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂...",
    ]

    try:

        for frame in frames:

            await asyncio.sleep(0.35)

            await message.edit_text(frame)

    except Exception:
        pass

    return message


# ============================================================
# MESSAGE SPLITTER
# ============================================================

def split_message(text, limit=3900):

    parts = []

    while len(text) > limit:

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

    if text:
        parts.append(text)

    return parts


# ============================================================
# INFORMATION ANSWER
# ============================================================

def build_answer(
    page,
    language
):

    title = page.get(
        "title",
        "Unknown"
    )

    extract = page.get(
        "extract",
        ""
    ).strip()

    if not extract:
        return None

    # Long answer.
    extract = extract[:12000]

    if language == "fa":

        header = (
            "𝕳𝖅𝕽𝟏⁹\n\n"
            f"موضوع: {title}\n\n"
            "اطلاعات:\n\n"
        )

    else:

        header = (
            "𝕳𝖅𝕽𝟏⁹\n\n"
            f"Topic: {title}\n\n"
            "Information:\n\n"
        )

    return (
        header
        + extract
        + f"\n\n{HZR_TAG}"
    )


# ============================================================
# MAIN MESSAGE
# ============================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text

    if not text:
        return

    text = normalize_text(text)

    if not text:
        return

    user_id = update.effective_user.id

    lower = text.casefold()

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if lower in {
        "help",
        "کمک",
        "/help"
    }:

        await help_command(
            update,
            context
        )

        return

    # --------------------------------------------------------
    # GREETING
    # --------------------------------------------------------

    greeting = get_greeting(text)

    if greeting:

        await update.message.reply_text(
            f"𝕳𝖅𝕽𝟏⁹\n\n"
            f"{greeting}\n\n"
            f"{HZR_TAG}"
        )

        return

    # --------------------------------------------------------
    # CALCULATOR
    # --------------------------------------------------------

    if looks_like_calculation(text):

        result = safe_calculate(text)

        if result is not None:

            await update.message.reply_text(
                f"𝕳𝖅𝕽𝟏⁹\n\n"
                f"{text} = "
                f"{format_number(result)}\n\n"
                f"{HZR_TAG}"
            )

            return

    # --------------------------------------------------------
    # FOLLOW-UP QUESTION
    # --------------------------------------------------------

    previous_topic = get_last_topic(user_id)

    follow_up_phrases = [
        "پایتختش",
        "پایتخت آن",
        "پایتختش چیست",
        "its capital",
        "what is its capital",
        "capital of it",
        "where is it",
    ]

    if (
        previous_topic
        and any(
            phrase in lower
            for phrase in follow_up_phrases
        )
    ):

        text = (
            "capital of "
            + previous_topic
        )

    # --------------------------------------------------------
    # QUERY
    # --------------------------------------------------------

    query = clean_query(text)

    if not query:
        query = text

    # --------------------------------------------------------
    # THINKING
    # --------------------------------------------------------

    thinking = await show_thinking(
        update.effective_chat.id
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    language = detect_language(text)

    results, search_language = (
        await search_in_best_language(
            query,
            language
        )
    )

    # --------------------------------------------------------
    # REMOVE THINKING
    # --------------------------------------------------------

    try:
        await thinking.delete()
    except Exception:
        pass

    # --------------------------------------------------------
    # NO RESULTS
    # --------------------------------------------------------

    if not results:

        await update.message.reply_text(
            f"𝕳𝖅𝕽𝟏⁹\n\n"
            f"I could not find reliable information for:\n\n"
            f"{query}\n\n"
            f"Try a more specific topic.\n\n"
            f"{HZR_TAG}"
        )

        return

    # --------------------------------------------------------
    # EXACT RESULT
    # --------------------------------------------------------

    exact = None

    for title in results:

        if title.casefold() == query.casefold():

            exact = title
            break

    # --------------------------------------------------------
    # MULTIPLE SUGGESTIONS
    # --------------------------------------------------------

    if (
        exact is None
        and len(results) > 1
        and len(query) <= 50
    ):

        remember(
            user_id,
            query
        )

        keyboard = make_suggestion_keyboard(
            results
        )

        await update.message.reply_text(
            f"𝕳𝖅𝕽𝟏⁹\n\n"
            f"Search suggestions for:\n"
            f"「{query}」\n\n"
            f"Choose a result:",
            reply_markup=keyboard
        )

        return

    # --------------------------------------------------------
    # SELECT RESULT
    # --------------------------------------------------------

    title = exact or results[0]

    page = await wikipedia_page(
        title,
        search_language
    )

    # English fallback.
    if (
        not page
        and search_language != "en"
    ):

        page = await wikipedia_page(
            title,
            "en"
        )

    # --------------------------------------------------------
    # PAGE FAILED
    # --------------------------------------------------------

    if not page:

        await update.message.reply_text(
            f"𝕳𝖅𝕽𝟏⁹\n\n"
            f"I found the topic, but I could not "
            f"load its detailed information.\n\n"
            f"{HZR_TAG}"
        )

        return

    remember(
        user_id,
        page["title"]
    )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    image = page.get("image")

    if image:

        try:

            await update.message.reply_photo(
                photo=image
            )

        except Exception as error:

            print(
                "Image error:",
                error
            )

    # --------------------------------------------------------
    # ANSWER
    # --------------------------------------------------------

    answer = build_answer(
        page,
        language
    )

    if not answer:
        return

    # --------------------------------------------------------
    # LONG ANSWER
    # --------------------------------------------------------

    for part in split_message(answer):

        try:

            await update.message.reply_text(
                part
            )

        except Exception as error:

            print(
                "Message error:",
                error
            )

            await update.message.reply_text(
                part.replace(
                    "<",
                    ""
                ).replace(
                    ">",
                    ""
                )
            )


# ============================================================
# SUGGESTION CALLBACK
# ============================================================

async def suggestion_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    data = query.data or ""

    if not data.startswith("wiki:"):
        return

    title = data[5:].strip()

    if not title:
        return

    language = detect_language(
        query.message.text or ""
    )

    search_language = (
        "fa"
        if language == "fa"
        else "en"
    )

    thinking = await show_thinking(
        query.message.chat.id
    )

    page = await wikipedia_page(
        title,
        search_language
    )

    if (
        not page
        and search_language != "en"
    ):

        page = await wikipedia_page(
            title,
            "en"
        )

    try:
        await thinking.delete()
    except Exception:
        pass

    if not page:

        await query.message.reply_text(
            f"𝕳𝖅𝕽𝟏⁹\n\n"
            f"Information could not be loaded.\n\n"
            f"{HZR_TAG}"
        )

        return

    remember(
        query.from_user.id,
        page["title"]
    )

    image = page.get("image")

    if image:

        try:

            await query.message.reply_photo(
                photo=image
            )

        except Exception:
            pass

    answer = build_answer(
        page,
        language
    )

    if answer:

        for part in split_message(answer):

            await query.message.reply_text(
                part
            )


# ============================================================
# WEBHOOK
# ============================================================

async def webhook_handler(request):

    secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if secret != WEBHOOK_SECRET:

        return web.Response(
            status=403,
            text="Forbidden"
        )

    try:

        data = await request.json()

    except Exception:

        return web.Response(
            status=400,
            text="Invalid JSON"
        )

    try:

        update = Update.de_json(
            data,
            APPLICATION.bot
        )

        await APPLICATION.update_queue.put(
            update
        )

    except Exception as error:

        print(
            "Webhook error:",
            error
        )

        return web.Response(
            status=500,
            text="Webhook error"
        )

    return web.Response(
        status=200,
        text="OK"
    )


# ============================================================
# HEALTH
# ============================================================

async def root_handler(request):

    return web.Response(
        text="𝕳𝖅𝕽𝟏⁹ AI Telegram Bot is online."
    )


async def health_handler(request):

    return web.json_response({
        "success": True,
        "service": "HZR19 AI Telegram Bot",
        "status": "online",
        "mode": "webhook"
    })


# ============================================================
# START SERVER
# ============================================================

async def start_server():

    global APPLICATION

    APPLICATION = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    APPLICATION.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    APPLICATION.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    APPLICATION.add_handler(
        CommandHandler(
            "status",
            status_command
        )
    )

    # Suggestion buttons
    APPLICATION.add_handler(
        CallbackQueryHandler(
            suggestion_callback,
            pattern=r"^wiki:"
        )
    )

    # Normal messages
    APPLICATION.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_handler
        )
    )

    # Initialize Telegram application
    await APPLICATION.initialize()
    await APPLICATION.start()

    webhook_url = (
        RENDER_EXTERNAL_URL
        + WEBHOOK_PATH
    )

    await APPLICATION.bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=False
    )

    print(
        "======================================"
    )

    print(
        "𝕳𝖅𝕽𝟏⁹ AI TELEGRAM BOT"
    )

    print(
        "MODE: WEBHOOK"
    )

    print(
        "WEBHOOK:",
        webhook_url
    )

    print(
        "STATUS: ONLINE"
    )

    print(
        "======================================"
    )

    # Web server
    app = web.Application()

    app.router.add_get(
        "/",
        root_handler
    )

    app.router.add_get(
        "/health",
        health_handler
    )

    app.router.add_get(
        "/api/status",
        health_handler
    )

    app.router.add_post(
        WEBHOOK_PATH,
        webhook_handler
    )

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    print(
        f"HTTP server running on port {PORT}"
    )

    try:

        await asyncio.Event().wait()

    finally:

        print(
            "Shutting down HZR19..."
        )

        try:
            await APPLICATION.bot.delete_webhook()
        except Exception:
            pass

        await runner.cleanup()

        await APPLICATION.stop()
        await APPLICATION.shutdown()

        global HTTP_SESSION

        if HTTP_SESSION:

            await HTTP_SESSION.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            start_server()
        )

    except KeyboardInterrupt:

        print(
            "HZR19 stopped."
)
