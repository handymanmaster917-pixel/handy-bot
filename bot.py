import os
import anthropic
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты Ханди, помощник HandySolution Batumi.
Услуги: электрика, сантехника, отделка, мебель, двери, освещение, ремонт под ключ.
Контакт: @HandySolution_Batumi, +995 593 488 423, Алексей.
Выезд для оценки бесплатный. Работаем в Батуми.
Для заявки: тип услуги, адрес, время, телефон.
Отвечай на языке клиента."""

user_histories = {}

MENU = ReplyKeyboardMarkup([
    [KeyboardButton("Вызвать мастера"), KeyboardButton("Услуги")],
    [KeyboardButton("Цены"), KeyboardButton("Контакты")]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_histories[uid] = []
    name = update.effective_user.first_name or "друг"
    await update.message.reply_text(
        "Привет, " + name + "!\n\n"
        "HandySolution Batumi — профессиональный ремонт.\n"
        "Выезд мастера БЕСПЛАТНО!\n\n"
        "Чем помочь?",
        reply_markup=MENU
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    if uid not in user_histories:
        user_histories[uid] = []

    if text == "Услуги":
        await update.message.reply_text(
            "Наши услуги:\n\nЭлектрика\nСантехника\nОтделка\nМебель\nДвери\nОсвещение\nРемонт под ключ",
            reply_markup=MENU
        )
        return
    if text == "Контакты":
        await update.message.reply_text(
            "Алексей\n+995 593 488 423\n@HandySolution_Batumi",
            reply_markup=MENU
        )
        return

    user_histories[uid].append({"role": "user", "content": text})
    if len(user_histories[uid]) > 20:
        user_histories[uid] = user_histories[uid][-20:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=user_histories[uid]
        )
        reply = r.content[0].text
    except Exception:
        reply = "Ошибка. Позвоните: +995 593 488 423"

    user_histories[uid].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply, reply_markup=MENU)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Ханди запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
