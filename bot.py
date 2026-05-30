import os
import anthropic
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты — Ханди, профессиональный виртуальный помощник компании HandySolution Batumi.

Компания HandySolution — это команда профессиональных мастеров в Батуми, Грузия.
Контакт: @HandySolution_Batumi | +995 593 488 423 | Алексей

УСЛУГИ И ПРИМЕРНЫЕ ЦЕНЫ:
⚡ Электрика — розетки, проводка, щитки, освещение
🚿 Сантехника — трубы, краны, унитазы, душевые
🪟 Отделка — штукатурка, покраска, обои
🪑 Мебель — сборка, установка, крепление
🚪 Двери и замки — установка, замена, ремонт
💡 Освещение — люстры, споты, LED
🏠 Ремонт под ключ — полный цикл

ВАЖНО:
- Выезд мастера для оценки БЕСПЛАТНЫЙ
- Выезд в день обращения
- Качество гарантировано
- Работаем чисто и аккуратно

Для оформления заявки собери:
1. Тип услуги
2. Адрес в Батуми
3. Удобное время
4. Номер телефона

Отвечай на русском, грузинском или английском — по языку клиента.
Будь вежлив, профессионален, конкретен. После сбора данных скажи что мастер свяжется в течение 30 минут."""

user_histories = {}

MAIN_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("🔧 Вызвать мастера"), KeyboardButton("📋 Наши услуги")],
    [KeyboardButton("💰 Цены"), KeyboardButton("📞 Контакты")],
    [KeyboardButton("⭐ О компании")]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "друг"
    user_histories[update.effective_user.id] = []
    await update.message.reply_text(
        f"👋 Привет, {user_name}!\n\n"
        f"Добро пожаловать в *HandySolution Batumi* 🔧\n\n"
        f"Мы — профессиональная команда мастеров в Батуми.\n"
        f"Электрика, сантехника, отделка, мебель и многое другое.\n\n"
        f"✅ *Выезд мастера для оценки — БЕСПЛАТНО*\n"
        f"⚡ Выезд в день обращения\n\n"
        f"Выберите что вас интересует 👇",
        parse_mode="Markdown",
        reply_markup=MAIN_MENU
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    # Быстрые ответы на кнопки
    quick_responses = {
        "📋 Наши услуги": (
            "🛠 *Наши услуги:*\n\n"
            "⚡ Электрика — розетки, проводка, щитки\n"
            "🚿 Сантехника — трубы, краны, душевые\n"
            "🪟 Отделка — штукатурка, покраска, обои\n"
            "🪑 Мебель — сборка и установка\n"
            "🚪 Двери и замки — установка и ремонт\n"
            "💡 Освещение — люстры, LED, споты\n"
            "🏠 Ремонт под ключ\n\n"
            "Напишите что нужно — мастер приедет сегодня! 💪"
        ),
        "📞 Контакты": (
            "📞 *Контакты HandySolution Batumi:*\n\n"
            "👤 Алексей\n"
            "📱 +995 593 488 423\n"
            "💬 @HandySolution_Batumi\n\n"
            "Или просто напишите мне прямо здесь — отвечу быстро! 🔧"
        ),
        "⭐ О компании": (
            "🏆 *О компании HandySolution Batumi:*\n\n"
            "Мы — команда профессиональных мастеров в Батуми.\n\n"
            "✅ Точная и аккуратная работа\n"
            "✅ Выезд в день обращения\n"
            "✅ Качество гарантировано\n"
            "✅ Работаем чисто и по делу\n"
            "✅ Бесплатная оценка на месте\n\n"
            "Доверьте ремонт профессионалам! 💪"
        ),
    }

    if text in quick_responses:
        await update.message.reply_text(
            quick_responses[text],
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        return

    if text in ["🔧 Вызвать мастера", "💰 Цены"]:
        user_histories[user_id] = []

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
    except Exception as e:
        reply = "Извините, произошла ошибка. Позвоните нам напрямую: +995 593 488 423"

    user_histories[user_id].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply, reply_markup=MAIN_MENU)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🔧 Ханди запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
