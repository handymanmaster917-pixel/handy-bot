import os
import anthropic
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ADMIN_ID = 8332704597

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты Ханди, помощник HandySolution Batumi. Компания делает профессиональный ремонт в Батуми, Грузия.
Контакт: @HandySolution_Batumi, +995 593 488 423, Алексей.
Услуги: электрика, сантехника, отделка, мебель, двери, освещение, ремонт под ключ.
Выезд для оценки БЕСПЛАТНЫЙ. Работаем в день обращения.
Когда клиент хочет вызвать мастера - собери: тип услуги, адрес в Батуми, удобное время, номер телефона.
Отвечай коротко и по делу на языке клиента."""

user_histories = {}
user_orders = {}
user_trials = {}

MAIN_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("🔧 Вызвать мастера"), KeyboardButton("📋 Услуги")],
    [KeyboardButton("💰 Цены"), KeyboardButton("📞 Контакты")],
    [KeyboardButton("⭐ Оставить отзыв")]
], resize_keyboard=True)

async def notify_admin(context, message):
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=message)
    except Exception as e:
        print(f"Admin notify error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_histories[uid] = []
    name = update.effective_user.first_name or "друг"
    
    # Проверяем пробный период
    if uid not in user_trials:
        user_trials[uid] = datetime.now()
    
    await update.message.reply_text(
        f"Привет, {name}! 👋\n\n"
        "🔧 *HandySolution Batumi*\n"
        "Профессиональный ремонт и монтаж\n\n"
        "✅ Выезд мастера — БЕСПЛАТНО\n"
        "⚡ Выезд в день обращения\n"
        "🏆 Качество гарантировано\n\n"
        "Чем могу помочь?",
        parse_mode="Markdown",
        reply_markup=MAIN_MENU
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    name = update.effective_user.first_name or "Клиент"
    username = f"@{update.effective_user.username}" if update.effective_user.username else "нет username"

    if uid not in user_histories:
        user_histories[uid] = []

    # Быстрые кнопки
    if text == "📋 Услуги":
        await update.message.reply_text(
            "🛠 *Наши услуги:*\n\n"
            "⚡ Электрика — розетки, проводка, щитки\n"
            "🚿 Сантехника — трубы, краны, душевые\n"
            "🪟 Отделка — штукатурка, покраска, обои\n"
            "🪑 Мебель — сборка и установка\n"
            "🚪 Двери и замки\n"
            "💡 Освещение — люстры, LED\n"
            "🏠 Ремонт под ключ\n\n"
            "Нажмите *Вызвать мастера* для заявки!",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        return

    if text == "📞 Контакты":
        await update.message.reply_text(
            "📞 *Контакты:*\n\n"
            "👤 Алексей\n"
            "📱 +995 593 488 423\n"
            "💬 @HandySolution_Batumi\n\n"
            "Или напишите прямо здесь — отвечу быстро!",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        return

    if text == "💰 Цены":
        await update.message.reply_text(
            "💰 *Цены:*\n\n"
            "Точная стоимость определяется после осмотра объекта.\n\n"
            "✅ *Выезд мастера для оценки — БЕСПЛАТНО!*\n\n"
            "Оставьте заявку и мастер приедет сегодня!",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        return

    if text == "⭐ Оставить отзыв":
        await update.message.reply_text(
            "⭐ *Оставьте ваш отзыв:*\n\n"
            "Напишите как прошла работа мастера — это очень важно для нас!\n\n"
            "🎁 *Первая неделя — бесплатно!*",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        # Уведомить админа
        await notify_admin(context,
            f"⭐ Клиент хочет оставить отзыв!\n"
            f"👤 {name} ({username})\n"
            f"ID: {uid}"
        )
        return

    if text == "🔧 Вызвать мастера":
        user_histories[uid] = [{"role": "user", "content": "Я хочу вызвать мастера"}]
        await update.message.reply_text(
            "Отлично! Давайте оформим заявку 📝\n\n"
            "Расскажите:\n"
            "1️⃣ Какая нужна услуга?\n"
            "2️⃣ Адрес в Батуми?\n"
            "3️⃣ Удобное время?\n"
            "4️⃣ Ваш номер телефона?",
            reply_markup=MAIN_MENU
        )
        return

    # Умный чат через Claude
    user_histories[uid].append({"role": "user", "content": text})
    if len(user_histories[uid]) > 20:
        user_histories[uid] = user_histories[uid][-20:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=user_histories[uid]
        )
        reply = response.content[0].text
        
        # Проверяем если клиент оставил контакты — уведомляем админа
        keywords = ["телефон", "номер", "адрес", "батуми", "улица", "+995", "заявк"]
        if any(kw in text.lower() for kw in keywords):
            await notify_admin(context,
                f"🔔 *НОВАЯ ЗАЯВКА!*\n\n"
                f"👤 Клиент: {name} ({username})\n"
                f"📱 ID: {uid}\n"
                f"💬 Сообщение: {text}\n\n"
                f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )

    except Exception:
        reply = "Извините, ошибка. Позвоните напрямую: +995 593 488 423"

    user_histories[uid].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply, reply_markup=MAIN_MENU)

async def handle_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Ханди запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
