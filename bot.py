import asyncio
import ast
import hashlib
import os
import re
import time
from collections import defaultdict, deque
from typing import Optional

import requests
from aiohttp import web

from telegram import Update
from telegram.constants import ChatAction
from telegram.error import BadRequest, RetryAfter
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


# =========================================================
# HZR19 CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

PORT = int(os.getenv("PORT", "10000"))

RENDER_EXTERNAL_URL = os.getenv(
    "RENDER_EXTERNAL_URL",
    "https://hzr19-ai-telegram-bot.onrender.com"
).rstrip("/")

WEBHOOK_PATH = "/telegram/webhook"

HZR_TAG = "@m19_goat"

HTTP_TIMEOUT = 12

TELEGRAM_MAX_LENGTH = 4000

CHAT_HISTORY_LIMIT = 8

THINKING_FRAMES = [
    "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂.",
    "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂..",
    "𝙃𝙕𝙍 𝙄𝙎 𝙏𝙃𝙄𝙉𝙆𝙄𝙉𝙂...",
]

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")


WEBHOOK_SECRET = hashlib.sha256(
    BOT_TOKEN.encode("utf-8")
).hexdigest()


# =========================================================
# HTTP SESSION
# =========================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": "HZR19/1.0"
})


# =========================================================
# WIKIPEDIA LANGUAGES
# =========================================================

LANGUAGES = {
    "fa": "fa",
    "ps": "ps",
    "ar": "ar",
    "en": "en",
    "ur": "ur",
    "hi": "hi",
    "tr": "tr",
    "de": "de",
    "fr": "fr",
    "es": "es",
    "it": "it",
    "pt": "pt",
    "ru": "ru",
    "zh": "zh",
    "ja": "ja",
    "ko": "ko",
    "nl": "nl",
    "pl": "pl",
    "sv": "sv",
    "id": "id",
    "ms": "ms",
    "bn": "bn",
    "ta": "ta",
    "te": "te",
    "he": "he",
    "uk": "uk",
    "vi": "vi",
    "th": "th",
}


# =========================================================
# LOCAL KNOWLEDGE
# =========================================================

LOCAL_KNOWLEDGE = {

    "افغانستان": {
        "fa": (
            "افغانستان کشوری در آسیای مرکزی و جنوبی است. "
            "پایتخت آن کابل است و ۳۴ ولایت دارد. "
            "این کشور با پاکستان، ایران، ترکمنستان، ازبکستان، "
            "تاجیکستان و چین مرز دارد."
        ),
        "ps": (
            "افغانستان په مرکزي او جنوبي اسیا کې یو هېواد دی. "
            "پلازمېنه یې کابل ده او ۳۴ ولایتونه لري."
        ),
        "en": (
            "Afghanistan is a country in Central and South Asia. "
            "Its capital is Kabul and it has 34 provinces."
        ),
    },

    "کابل": {
        "fa": (
            "کابل پایتخت افغانستان و یکی از مهم‌ترین شهرهای این کشور است. "
            "این شهر در میان کوه‌ها و در یک دره قرار گرفته است."
        ),
        "en": (
            "Kabul is the capital and one of the major cities of Afghanistan."
        ),
    },

    "افغانستان چیست": {
        "fa": (
            "افغانستان کشوری در آسیای مرکزی و جنوبی است "
            "و پایتخت آن کابل است."
        ),
        "en": (
            "Afghanistan is a country in Central and South Asia, "
            "with Kabul as its capital."
        ),
    },
}


# =========================================================
# STOP WORDS
# =========================================================

STOP_WORDS = {

    "fa": {
        "درباره",
        "درباره‌ی",
        "راجع",
        "راجع‌به",
        "در",
        "مورد",
        "برای",
        "چی",
        "چه",
        "است",
        "هست",
        "بگو",
        "بگویید",
        "بده",
        "ده",
        "را",
        "از",
        "به",
        "یک",
        "این",
        "آن",
        "که",
        "و",
        "یا",
        "می",
        "شود",
        "شد",
        "کن",
        "کنید",
        "لطفا",
        "لطفاً",
        "معلومات",
        "اطلاعات",
        "توضیح",
        "توضیحی",
    },

    "ps": {
        "درباره",
        "په",
        "اړه",
        "کې",
        "څه",
        "څوک",
        "دی",
        "ده",
        "راکړه",
        "ووایه",
        "معلومات",
        "او",
        "د",
        "ته",
    },

    "ar": {
        "عن",
        "حول",
        "ما",
        "هو",
        "هي",
        "من",
        "في",
        "الى",
        "إلى",
        "هذا",
        "هذه",
        "معلومات",
        "اشرح",
        "قل",
        "لي",
    },

    "en": {
        "about",
        "tell",
        "me",
        "give",
        "information",
        "on",
        "what",
        "is",
        "are",
        "the",
        "a",
        "an",
        "of",
        "for",
        "please",
        "explain",
        "describe",
        "who",
        "where",
    },
}


# =========================================================
# MEMORY
# =========================================================

chat_history = defaultdict(
    lambda: deque(
        maxlen=CHAT_HISTORY_LIMIT
    )
)


# =========================================================
# TEXT UTILITIES
# =========================================================

def normalize_text(text: str) -> str:

    text = text or ""

    replacements = {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "ـ": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def remove_urls(text: str) -> str:

    text = re.sub(
        r"https?://\S+",
        "",
        text
    )

    text = re.sub(
        r"www\.\S+",
        "",
        text
    )

    return re.sub(
        r"[ \t]+",
        " ",
        text
    ).strip()


def split_message(
    text: str,
    limit: int = TELEGRAM_MAX_LENGTH
):

    if len(text) <= limit:
        return [text]

    parts = []

    while len(text) > limit:

        cut = text.rfind(
            "\n",
            0,
            limit
        )

        if cut < limit * 0.55:

            cut = text.rfind(
                " ",
                0,
                limit
            )

        if cut < limit * 0.55:
            cut = limit

        parts.append(
            text[:cut].strip()
        )

        text = text[cut:].strip()

    if text:
        parts.append(text)

    return parts


# =========================================================
# LANGUAGE DETECTION
# =========================================================

def detect_language(text: str) -> str:

    text = normalize_text(text)

    if not text:
        return "en"

    pashto_count = len(
        re.findall(
            r"[ځڅډړږښګڼټژ]",
            text
        )
    )

    persian_count = len(
        re.findall(
            r"[\u067E\u0686\u0698\u06AF\u06CC\u06A9\u06D0]",
            text
        )
    )

    arabic_count = len(
        re.findall(
            r"[\u0621-\u063A\u0641-\u064A]",
            text
        )
    )

    russian_count = len(
        re.findall(
            r"[\u0400-\u04FF]",
            text
        )
    )

    chinese_count = len(
        re.findall(
            r"[\u4E00-\u9FFF]",
            text
        )
    )

    japanese_count = len(
        re.findall(
            r"[\u3040-\u30FF]",
            text
        )
    )

    korean_count = len(
        re.findall(
            r"[\uAC00-\uD7AF]",
            text
        )
    )

    if pashto_count:
        return "ps"

    if persian_count:
        return "fa"

    if arabic_count:
        return "ar"

    if russian_count:
        return "ru"

    if chinese_count:
        return "zh"

    if japanese_count:
        return "ja"

    if korean_count:
        return "ko"

    return "en"


# =========================================================
# WIKIPEDIA
# =========================================================

def wikipedia_api(lang: str) -> str:

    if lang not in LANGUAGES:
        lang = "en"

    return (
        f"https://{lang}.wikipedia.org/w/api.php"
    )


def wikipedia_search(
    query: str,
    lang: str,
    limit: int = 8
):

    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "utf8": 1,
    }

    try:

        response = SESSION.get(
            wikipedia_api(lang),
            params=params,
            timeout=HTTP_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        return (
            data
            .get("query", {})
            .get("search", [])
        )

    except Exception as error:

        print(
            "Wikipedia search error:",
            repr(error)
        )

        return []


def score_result(
    query: str,
    result: dict
) -> int:

    query = normalize_text(
        query
    ).lower()

    title = normalize_text(
        result.get(
            "title",
            ""
        )
    ).lower()

    snippet = normalize_text(
        re.sub(
            r"<.*?>",
            " ",
            result.get(
                "snippet",
                ""
            )
        )
    ).lower()

    score = 0

    if title == query:
        score += 100

    if query in title:
        score += 70

    query_words = set(
        query.split()
    )

    title_words = set(
        title.split()
    )

    snippet_words = set(
        snippet.split()
    )

    score += len(
        query_words & title_words
    ) * 15

    score += len(
        query_words & snippet_words
    ) * 3

    return score


def choose_best_result(
    query: str,
    results: list
):

    if not results:
        return None

    return max(
        results,
        key=lambda result:
        score_result(
            query,
            result
        )
    )


def wikipedia_page(
    title: str,
    lang: str
):

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|pageimages",
        "explaintext": 1,
        "exintro": 0,
        "redirects": 1,
        "titles": title,
        "pithumbsize": 900,
    }

    try:

        response = SESSION.get(
            wikipedia_api(lang),
            params=params,
            timeout=HTTP_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        pages = (
            data
            .get("query", {})
            .get("pages", {})
        )

        if not pages:
            return None

        page = next(
            iter(pages.values())
        )

        if "missing" in page:
            return None

        extract = page.get(
            "extract",
            ""
        )

        extract = remove_urls(
            extract
        )

        extract = re.sub(
            r"\n{3,}",
            "\n\n",
            extract
        )

        return {
            "title": page.get(
                "title",
                ""
            ),
            "extract": extract.strip(),
            "image": (
                page
                .get("thumbnail", {})
                .get("source")
            ),
        }

    except Exception as error:

        print(
            "Wikipedia page error:",
            repr(error)
        )

        return None


def wikipedia_lookup(
    query: str,
    lang: str
):

    results = wikipedia_search(
        query,
        lang,
        8
    )

    best = choose_best_result(
        query,
        results
    )

    if not best:
        return None

    return wikipedia_page(
        best.get(
            "title",
            ""
        ),
        lang
    )


# =========================================================
# TOPIC UNDERSTANDING
# =========================================================

def extract_topic(
    query: str
) -> str:

    query = normalize_text(
        query
    )

    patterns = [

        r"^درباره\s+(.+?)\s+(?:بگو|بگویید)$",

        r"^راجع(?: به|‌به)\s+(.+)$",

        r"^در مورد\s+(.+)$",

        r"^در باره\s+(.+)$",

        r"^about\s+(.+)$",

        r"^tell me about\s+(.+)$",
    ]

    for pattern in patterns:

        match = re.match(
            pattern,
            query,
            re.IGNORECASE
        )

        if match:

            return match.group(
                1
            ).strip()

    return query.strip()


def get_last_topic(
    chat_id: int
):

    history = chat_history.get(
        chat_id
    )

    if not history:
        return None

    for item in reversed(history):

        if item.get("topic"):
            return item["topic"]

    return None


def clean_query(
    user_text: str,
    history_topic: Optional[str] = None
):

    text = normalize_text(
        user_text
    )

    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    text = re.sub(
        r"@\w+",
        " ",
        text
    )

    text = re.sub(
        r"^/[\w_]+",
        " ",
        text
    )

    text = re.sub(
        r"[؟?!،؛:,.]+",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    references = [

        "پایتختش",
        "تاریخچه اش",
        "تاریخچه‌اش",
        "جمعیتش",
        "زبانش",
        "مساحتش",
        "رئیس جمهورش",
        "رئیس‌جمهورش",
        "این کشور",
        "آن کشور",

        "its capital",
        "its population",
        "its history",
        "where is it",
    ]

    if history_topic:

        for reference in references:

            if reference.lower() in text.lower():

                return (
                    f"{history_topic} {text}"
                )

    language = detect_language(
        text
    )

    stop_words = STOP_WORDS.get(
        language,
        set()
    )

    words = text.split()

    cleaned = [
        word
        for word in words
        if word.lower()
        not in stop_words
    ]

    result = " ".join(
        cleaned
    ).strip()

    if len(result) < 2:
        return text

    return result


# =========================================================
# LOCAL KNOWLEDGE
# =========================================================

def local_knowledge(
    query: str,
    language: str
):

    q = normalize_text(
        query
    ).lower()

    for key, languages in LOCAL_KNOWLEDGE.items():

        key_norm = normalize_text(
            key
        ).lower()

        if (
            q == key_norm
            or key_norm in q
            or q in key_norm
        ):

            return (
                languages.get(language)
                or languages.get("en")
            )

    return None


# =========================================================
# SAFE CALCULATOR
# =========================================================

ALLOWED_OPERATORS = {

    ast.Add:
        lambda a, b: a + b,

    ast.Sub:
        lambda a, b: a - b,

    ast.Mult:
        lambda a, b: a * b,

    ast.Div:
        lambda a, b: a / b,

    ast.FloorDiv:
        lambda a, b: a // b,

    ast.Mod:
        lambda a, b: a % b,

    ast.Pow:
        lambda a, b: a ** b,

    ast.USub:
        lambda a: -a,

    ast.UAdd:
        lambda a: +a,
}


def safe_calculate(
    expression: str
):

    expression = expression.strip()

    if len(expression) > 100:
        return None

    expression = (
        expression
        .replace("×", "*")
        .replace("÷", "/")
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
    )

    if not re.fullmatch(
        r"[0-9+\-*/%.() \t]+",
        expression
    ):
        return None

    try:

        tree = ast.parse(
            expression,
            mode="eval"
        )

        def evaluate(node):

            if isinstance(
                node,
                ast.Expression
            ):
                return evaluate(
                    node.body
                )

            if isinstance(
                node,
                ast.Constant
            ):

                if isinstance(
                    node.value,
                    (int, float)
                ):
                    return node.value

                raise ValueError

            if isinstance(
                node,
                ast.BinOp
            ):

                operation = (
                    ALLOWED_OPERATORS.get(
                        type(node.op)
                    )
                )

                if not operation:
                    raise ValueError

                left = evaluate(
                    node.left
                )

                right = evaluate(
                    node.right
                )

                if (
                    abs(left) > 10**100
                    or abs(right) > 10**100
                ):
                    raise ValueError

                return operation(
                    left,
                    right
                )

            if isinstance(
                node,
                ast.UnaryOp
            ):

                operation = (
                    ALLOWED_OPERATORS.get(
                        type(node.op)
                    )
                )

                if not operation:
                    raise ValueError

                return operation(
                    evaluate(
                        node.operand
                    )
                )

            raise ValueError

        result = evaluate(tree)

        if isinstance(
            result,
            float
        ):

            if result.is_integer():

                return str(
                    int(result)
                )

            return f"{result:.10g}"

        return str(result)

    except Exception:

        return None


def extract_calculation(
    text: str
):

    cleaned = normalize_text(
        text
    ).lower()

    patterns = [

        r"^(?:حساب کن|محاسبه کن|جواب)\s*[:：]?\s*(.+)$",

        r"^(?:calculate|calc)\s+(.+)$",

        r"^=\s*(.+)$",
    ]

    for pattern in patterns:

        match = re.match(
            pattern,
            cleaned
        )

        if match:

            expression = match.group(
                1
            ).strip()

            result = safe_calculate(
                expression
            )

            if result is not None:
                return result

    normalized_expression = (
        cleaned
        .replace("×", "*")
        .replace("÷", "/")
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
    )

    if re.fullmatch(
        r"[0-9+\-*/%.() \t]+",
        normalized_expression
    ):

        return safe_calculate(
            normalized_expression
        )

    return None


# =========================================================
# ANSWER BUILDER
# =========================================================

def make_answer(
    user_text: str,
    query: str,
    language: str,
    page: Optional[dict]
):

    calculation = extract_calculation(
        user_text
    )

    if calculation is not None:

        if language == "fa":

            return (
                f"نتیجه:\n{calculation}",
                None,
                "محاسبه"
            )

        if language == "ps":

            return (
                f"پایله:\n{calculation}",
                None,
                "محاسبه"
            )

        if language == "ar":

            return (
                f"النتيجة:\n{calculation}",
                None,
                "calculation"
            )

        return (
            f"Result:\n{calculation}",
            None,
            "calculation"
        )

    local = local_knowledge(
        query,
        language
    )

    if local:

        return (
            local,
            None,
            extract_topic(query)
        )

    if not page:

        messages = {

            "fa": (
                "نتیجه مناسبی برای این درخواست پیدا نکردم. "
                "موضوع را کمی دقیق‌تر بنویس."
            ),

            "ps": (
                "د دې غوښتنې لپاره مناسبه پایله پیدا نه شوه. "
                "موضوع لږه روښانه ولیکه."
            ),

            "ar": (
                "لم أجد نتيجة مناسبة لهذا الطلب. "
                "اكتب الموضوع بشكل أكثر دقة."
            ),

            "en": (
                "I could not find a suitable result. "
                "Try sending the topic more precisely."
            ),
        }

        return (
            messages.get(
                language,
                messages["en"]
            ),
            None,
            extract_topic(query)
        )

    title = page.get(
        "title",
        ""
    ).strip()

    extract = page.get(
        "extract",
        ""
    ).strip()

    image = page.get(
        "image"
    )

    if not extract:
        extract = title

    if len(extract) > 7500:

        extract = (
            extract[:7500]
            .rsplit(" ", 1)[0]
            + "..."
        )

    answer = (
        f"{title}\n\n"
        f"{extract}"
    )

    return (
        answer,
        image,
        title
    )


# =========================================================
# THINKING ANIMATION
# =========================================================

async def start_thinking(
    message
):

    stop_event = asyncio.Event()

    async def animate():

        index = 0

        while not stop_event.is_set():

            frame = THINKING_FRAMES[
                index % len(
                    THINKING_FRAMES
                )
            ]

            index += 1

            try:

                await message.edit_text(
                    frame
                )

            except RetryAfter as error:

                await asyncio.sleep(
                    float(
                        error.retry_after
                    )
                )

            except BadRequest:
                pass

            except Exception:
                pass

            try:

                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=0.9
                )

            except asyncio.TimeoutError:
                pass

    task = asyncio.create_task(
        animate()
    )

    return (
        stop_event,
        task
    )


async def stop_thinking(
    message,
    stop_event,
    task
):

    stop_event.set()

    try:
        await task
    except Exception:
        pass

    try:
        await message.delete()
    except Exception:
        pass


# =========================================================
# MEMORY
# =========================================================

def remember(
    chat_id: int,
    user_text: str,
    answer: str,
    topic: Optional[str]
):

    chat_history[chat_id].append({

        "user": user_text[:500],

        "answer": answer[:1000],

        "topic": topic,

        "time": time.time(),
    })


# =========================================================
# SEND IMAGE FIRST
# THEN SEND TEXT
# =========================================================

async def send_final_answer(
    update: Update,
    answer: str,
    image_url: Optional[str]
):

    if not update.message:
        return

    # -----------------------------------------------------
    # 1. IMAGE FIRST
    # -----------------------------------------------------

    if image_url:

        try:

            await update.message.reply_photo(
                photo=image_url
            )

        except Exception as error:

            print(
                "IMAGE ERROR:",
                repr(error)
            )

    # -----------------------------------------------------
    # 2. TEXT AFTER IMAGE
    # -----------------------------------------------------

    answer = remove_urls(
        answer
    ).strip()

    answer = (
        answer.rstrip()
        + "\n\n"
        + HZR_TAG
    )

    for part in split_message(
        answer
    ):

        try:

            await update.message.reply_text(
                part,
                disable_web_page_preview=True
            )

        except Exception as error:

            print(
                "TEXT SEND ERROR:",
                repr(error)
            )


# =========================================================
# MESSAGE HANDLER
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if (
        not update.message
        or not update.message.text
    ):
        return

    user_text = update.message.text.strip()

    if not user_text:
        return

    chat_id = update.effective_chat.id

    language = detect_language(
        user_text
    )

    last_topic = get_last_topic(
        chat_id
    )

    query = clean_query(
        user_text,
        last_topic
    )

    thinking = await update.message.reply_text(
        THINKING_FRAMES[0]
    )

    stop_event, thinking_task = (
        await start_thinking(
            thinking
        )
    )

    try:

        await update.message.chat.send_action(
            action=ChatAction.TYPING
        )

        await asyncio.sleep(
            0.35
        )

        topic = extract_topic(
            query
        )

        # Search in the user's language.
        page = await asyncio.to_thread(
            wikipedia_lookup,
            topic,
            language
        )

        # English fallback.
        if (
            not page
            and language != "en"
        ):

            page = await asyncio.to_thread(
                wikipedia_lookup,
                topic,
                "en"
            )

        answer, image, final_topic = (
            make_answer(
                user_text,
                query,
                language,
                page
            )
        )

        remember(
            chat_id,
            user_text,
            answer,
            final_topic
        )

        await stop_thinking(
            thinking,
            stop_event,
            thinking_task
        )

        # IMPORTANT:
        # send_final_answer sends the image FIRST.
        await send_final_answer(
            update,
            answer,
            image
        )

    except Exception as error:

        print(
            "HANDLER ERROR:",
            repr(error)
        )

        await stop_thinking(
            thinking,
            stop_event,
            thinking_task
        )

        try:

            await update.message.reply_text(
                "An error occurred while processing the request."
                "\n\n"
                + HZR_TAG
            )

        except Exception:
            pass


# =========================================================
# /START
# =========================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "𝕳𝖅𝕽𝟏⁹\n\n"
        "Intelligent Information System\n\n"
        "Ask a question, enter a topic, "
        "or send a calculation.\n\n"
        "Examples:\n"
        "• Afghanistan\n"
        "• What is Afghanistan?\n"
        "• Tell me about football\n"
        "• What is the capital of France?\n"
        "• 25 × 4\n\n"
        "Languages: Persian, Pashto, Arabic, "
        "English and more.\n\n"
        "No external AI API required.\n\n"
        f"{HZR_TAG}"
    )

    await update.message.reply_text(
        text
    )


# =========================================================
# /HELP
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "𝕳𝖅𝕽𝟏⁹\n\n"
        "Commands\n\n"
        "/start — Start HZR19\n"
        "/help — Show help\n"
        "/status — Show system status\n\n"
        "You can also simply send a message.\n\n"
        "Examples:\n"
        "What is Afghanistan?\n"
        "Tell me about Messi\n"
        "What is the capital of Japan?\n"
        "25 × 8 + 10\n\n"
        f"{HZR_TAG}"
    )

    await update.message.reply_text(
        text
    )


# =========================================================
# /STATUS
# =========================================================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "𝕳𝖅𝕽𝟏⁹ STATUS\n\n"
        "System: ONLINE\n"
        "Mode: WEBHOOK\n"
        "External AI: OFF\n"
        "Wikipedia Search: ON\n"
        "Relevant Images: ON\n"
        "Short Memory: ON\n"
        "Calculator: ON\n"
        "Multilingual: ON\n\n"
        f"{HZR_TAG}"
    )

    await update.message.reply_text(
        text
    )


# =========================================================
# WEB SERVER
# =========================================================

APPLICATION = None


async def health(
    request
):

    return web.Response(
        text="HZR19 ONLINE",
        status=200
    )


async def status_api(
    request
):

    return web.json_response({

        "service": "HZR19",

        "status": "online",

        "mode": "webhook",

        "external_ai": False,

        "wikipedia": True,

        "images": True,

        "memory": True,

        "calculator": True,

        "multilingual": True,
    })


async def telegram_webhook(
    request
):

    secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if secret != WEBHOOK_SECRET:

        return web.Response(
            text="Forbidden",
            status=403
        )

    try:

        data = await request.json()

        update = Update.de_json(
            data,
            APPLICATION.bot
        )

        await APPLICATION.update_queue.put(
            update
        )

        return web.Response(
            text="OK",
            status=200
        )

    except Exception as error:

        print(
            "WEBHOOK ERROR:",
            repr(error)
        )

        return web.Response(
            text="Bad Request",
            status=400
        )


# =========================================================
# START WEBHOOK SERVER
# =========================================================

async def start_server():

    global APPLICATION

    APPLICATION = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

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

    APPLICATION.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    # -----------------------------------------------------
    # WEBHOOK ONLY
    # -----------------------------------------------------

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
        "HZR19 WEBHOOK ACTIVE"
    )

    print(
        "Webhook:",
        webhook_url
    )

    print(
        "======================================"
    )

    app = web.Application()

    app.router.add_get(
        "/",
        health
    )

    app.router.add_get(
        "/health",
        health
    )

    app.router.add_get(
        "/api/status",
        status_api
    )

    app.router.add_post(
        WEBHOOK_PATH,
        telegram_webhook
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
        f"HZR19 server running on port {PORT}"
    )

    return runner


# =========================================================
# SHUTDOWN
# =========================================================

async def shutdown_server(
    runner
):

    global APPLICATION

    try:

        if APPLICATION:

            try:

                await APPLICATION.bot.delete_webhook(
                    drop_pending_updates=False
                )

            except Exception:
                pass

            await APPLICATION.stop()

            await APPLICATION.shutdown()

    finally:

        await runner.cleanup()


# =========================================================
# MAIN
# =========================================================

async def main():

    runner = await start_server()

    try:

        while True:

            await asyncio.sleep(
                3600
            )

    except (
        KeyboardInterrupt,
        asyncio.CancelledError
    ):

        pass

    finally:

        await shutdown_server(
            runner
        )


if __name__ == "__main__":

    asyncio.run(main())
