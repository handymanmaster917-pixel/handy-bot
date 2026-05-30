import os
import anthropic
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты — Ханди, профессиональный виртуальный помощник компании HandySolution Batumi.
Компания HandySolution — команда профессиональных мастеров в Батуми, Грузия.
Контакт: @HandySolution_Batumi | +995 593 488 423 | Алексей

УСЛУГИ:
- Электрика: розетки, проводка, щитки, освещение
- Сантехника: трубы, краны, унитазы, душевые
- Отделка: штукатурка, покраска, обои
- Мебель: сборка, установка
- Двери и замки: установка, замена, ремонт
- Освещение: люстры, споты, LED
- Ремонт под ключ

Выезд мастера для оценки БЕСПЛАТНЫЙ. Выезд в день обращения.
Для заявки собери: тип услуги, адрес в Батуми, удобное время, номер телефона.
Отвечай на русском, грузинском или английском языке клиента."""

user_histories = {}

MAIN_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("Вызвать мастера"), KeyboardButton("Наши услуги")],
    [KeyboardButton("Цены"), KeyboardButton("Контакты")],
    [KeyboardButton("О компании")]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "друг"
    user_histories[update.effective_user.id] = []
    await update.message.reply_text(
        "Привет, " + user_name + "!\n\n"
        "Добро пожаловать в HandySolution Batumi!\n\n"
        "Профессиональный ремонт и монтаж в Батуми.\n"
        "Выезд мастера для оценки БЕСПЛАТНО!\n"
        "Выезд в день обращения.\n\n"
        "Выберите что вас интересует:",
        reply_markup=MAIN_MENU
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    quick = {
        "Наши услуги": "Наши услуги:\n\nЭлектрика\nСантехника\nОтделка\nМебель\nДвери и замки\nОсвещение\nРемонт под ключ\n\nНапишите что нужно!",
        "Контакты": "Контакты HandySolution Batumi:\n\nАлексей\n+995 593 488 423\n@HandySolution_Batumi",
        "О компании": "HandySolution Batumi:\n\nТочная и аккуратная работа\nВыезд в день обращения\nКачество гарантировано\nБесплатная оценка на месте",
    }

    if text in quick:
        await update.message.reply_text(quick[text], reply_markup=MAIN_MENU)
        return

    user_histories[user_id].append({"role": "user", "content": text})
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=user_histories[user_id]
        )
        reply = response.content[0].text
    except Exception:
        reply = "Извините, ошибка. Позвоните: +995 593 488 423"

    user_histories[user_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply, reply_markup=MAIN_MENU)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Ханди запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
