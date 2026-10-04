import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==========================================
# HZR19 AI TELEGRAM BOT
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

PORT = int(os.getenv("PORT", "10000"))

FOOTER = """
━━━━━━━━━━━━━━━━━━━━
        𝕳𝖅𝕽𝟏⁹
      2010-206
━━━━━━━━━━━━━━━━━━━━
"""

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")


# ==========================================
# RENDER HEALTH CHECK
# ==========================================

async def health(request):
    return web.Response(
        text="HZR19 AI Telegram Bot is online."
    )


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    print(f"HZR19 web server running on port {PORT}")


# ==========================================
# THINKING ANIMATION
# ==========================================

async def thinking_animation(message):
    dots = 1

    try:
        while True:

            text = "HZR IS THINKING" + "." * dots

            await message.edit_text(text)

            dots += 1

            if dots > 3:
                dots = 1

            await asyncio.sleep(0.7)

    except asyncio.CancelledError:
        pass

    except Exception:
        pass


# ==========================================
# START COMMAND
# ==========================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "سلام.\n\n"
        "من HZR19 هستم.\n\n"
        "موضوع یا سؤال خود را بفرستید؛ "
        "حتی اگر فقط نام یک موضوع را بنویسید، "
        "می‌توانم درباره آن توضیح بدهم."
        + FOOTER
    )


# ==========================================
# MESSAGE HANDLER
# ==========================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    user_text = update.message.text

    if not user_text:
        return

    user_text = user_text.strip()

    if not user_text:
        return

    # Thinking message
    thinking_message = await update.message.reply_text(
        "HZR IS THINKING."
    )

    # Start animation
    animation_task = asyncio.create_task(
        thinking_animation(thinking_message)
    )

    try:

        # --------------------------------------
        # TEMPORARY AI RESPONSE
        # --------------------------------------
        #
        # در مرحله بعد این قسمت را به موتور AI
        # واقعی متصل می‌کنیم.
        #

        await asyncio.sleep(2)

        answer = (
            f"موضوع دریافت شد: {user_text}\n\n"
            "موتور هوش مصنوعی HZR19 هنوز متصل نشده است. "
            "در مرحله بعد، سیستم هوشمند پاسخ‌گویی، "
            "جستجوی اطلاعات و ارسال تصویر به این بخش "
            "اضافه خواهد شد."
        )

        final_answer = answer + FOOTER

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

        # Send final response
        await update.message.reply_text(
            final_answer
        )

    except Exception as error:

        animation_task.cancel()

        try:
            await animation_task
        except asyncio.CancelledError:
            pass

        try:
            await thinking_message.delete()
        except Exception:
            pass

        print("ERROR:", error)

        await update.message.reply_text(
            "در پردازش درخواست خطایی رخ داد."
            + FOOTER
        )


# ==========================================
# MAIN
# ==========================================

async def main():

    await start_web_server()

    application = (
        Application.builder()
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

    print("HZR19 Telegram Bot starting...")

    await application.initialize()
    await application.start()

    await application.updater.start_polling()

    print("HZR19 Telegram Bot is running.")

    try:
        while True:
            await asyncio.sleep(3600)

    except asyncio.CancelledError:
        pass

    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
