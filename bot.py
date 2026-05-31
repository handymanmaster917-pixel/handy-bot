import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = 8332704597  # @batumihandy

# Состояния диалога
user_states = {}  # uid -> state
user_orders = {}  # uid -> dict с данными заказа

STATES = {
    "IDLE": 0,
    "ASK_SERVICE": 1,
    "ASK_ADDRESS": 2,
    "ASK_TIME": 3,
    "ASK_PHONE": 4,
}

MENU = ReplyKeyboardMarkup([
    [KeyboardButton("🔧 Вызвать мастера"), KeyboardButton("📋 Услуги")],
    [KeyboardButton("💰 Цены"), KeyboardButton("📞 Контакты")],
    [KeyboardButton("⭐ Оставить отзыв")]
], resize_keyboard=True)

SERVICES_KB = ReplyKeyboardMarkup([
    [KeyboardButton("⚡ Электрика"), KeyboardButton("🚿 Сантехника")],
    [KeyboardButton("🏠 Отделка"), KeyboardButton("🪑 Сборка мебели")],
    [KeyboardButton("🚪 Двери"), KeyboardButton("💡 Освещение")],
    [KeyboardButton("🔑 Ремонт под ключ"), KeyboardButton("❓ Другое")]
], resize_keyboard=True)

async def notify_admin(context, text):
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception as e:
        print(f"Ошибка уведомления: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_states[uid] = STATES["IDLE"]
    user_orders[uid] = {}
    name = update.effective_user.first_name or "друг"
    await update.message.reply_text(
        f"Привет, {name}! 👋\n\n"
        "🔧 *HandySolution Batumi*\n"
        "Профессиональный ремонт и монтаж\n\n"
        "✅ Выезд мастера — БЕСПЛАТНО\n"
        "⚡ Выезд в день обращения\n"
        "🏆 Качество гарантировано\n\n"
        "Чем могу помочь?",
        reply_markup=MENU,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    username = update.effective_user.first_name or "Клиент"

    if uid not in user_states:
        user_states[uid] = STATES["IDLE"]
        user_orders[uid] = {}

    state = user_states[uid]

    # --- Обработка кнопок меню (всегда доступны) ---
    if text == "📋 Услуги":
        user_states[uid] = STATES["IDLE"]
        await update.message.reply_text(
            "📋 *Наши услуги:*\n\n"
            "⚡ Электрика\n"
            "🚿 Сантехника\n"
            "🏠 Отделка\n"
            "🪑 Сборка мебели\n"
            "🚪 Установка дверей\n"
            "💡 Освещение\n"
            "🔑 Ремонт под ключ\n\n"
            "Выезд для оценки — БЕСПЛАТНО!",
            reply_markup=MENU,
            parse_mode="Markdown"
        )
        return

    if text == "📞 Контакты":
        user_states[uid] = STATES["IDLE"]
        await update.message.reply_text(
            "📞 *Контакты:*\n\n"
            "👤 Алексей\n"
            "📱 +995 593 488 423\n"
            "💬 @HandySolution_Batumi",
            reply_markup=MENU,
            parse_mode="Markdown"
        )
        return

    if text == "💰 Цены":
        user_states[uid] = STATES["IDLE"]
        await update.message.reply_text(
            "💰 *Цены:*\n\n"
            "Стоимость зависит от объёма работ.\n"
            "Выезд мастера для оценки — *БЕСПЛАТНО*!\n\n"
            "Позвоните для уточнения: +995 593 488 423",
            reply_markup=MENU,
            parse_mode="Markdown"
        )
        return

    if text == "⭐ Оставить отзыв":
        user_states[uid] = STATES["IDLE"]
        await update.message.reply_text(
            "⭐ Напишите ваш отзыв — мы передадим его команде!\n\n"
            "Спасибо, что выбрали нас!",
            reply_markup=MENU
        )
        return

    # --- Начало заказа ---
    if text == "🔧 Вызвать мастера":
        user_states[uid] = STATES["ASK_SERVICE"]
        user_orders[uid] = {}
        await update.message.reply_text(
            "Отлично! Давайте оформим заявку.\n\n"
            "1️⃣ Какая услуга нужна?",
            reply_markup=SERVICES_KB
        )
        return

    # --- Шаги заказа ---
    if state == STATES["ASK_SERVICE"]:
        user_orders[uid]["service"] = text
        user_states[uid] = STATES["ASK_ADDRESS"]
        await update.message.reply_text(
            f"✅ Услуга: {text}\n\n"
            "2️⃣ Ваш адрес в Батуми?\n"
            "(улица, номер дома, квартира)",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if state == STATES["ASK_ADDRESS"]:
        user_orders[uid]["address"] = text
        user_states[uid] = STATES["ASK_TIME"]
        await update.message.reply_text(
            f"✅ Адрес записал!\n\n"
            "3️⃣ Удобное время для визита мастера?\n"
            "(например: сегодня после 15:00, завтра утром)"
        )
        return

    if state == STATES["ASK_TIME"]:
        user_orders[uid]["time"] = text
        user_states[uid] = STATES["ASK_PHONE"]
        await update.message.reply_text(
            "4️⃣ Ваш номер телефона?\n"
            "(для связи мастера с вами)"
        )
        return

    if state == STATES["ASK_PHONE"]:
        user_orders[uid]["phone"] = text
        user_states[uid] = STATES["IDLE"]

        order = user_orders[uid]

        # Подтверждение клиенту
        await update.message.reply_text(
            "✅ *Заявка принята!*\n\n"
            f"🔧 Услуга: {order.get('service')}\n"
            f"📍 Адрес: {order.get('address')}\n"
            f"🕐 Время: {order.get('time')}\n"
            f"📱 Телефон: {order.get('phone')}\n\n"
            "Мастер свяжется с вами в ближайшее время!\n"
            "По вопросам: +995 593 488 423 (Алексей)",
            reply_markup=MENU,
            parse_mode="Markdown"
        )

        # Уведомление админу
        await notify_admin(
            context,
            f"🔔 НОВАЯ ЗАЯВКА!\n\n"
            f"👤 Клиент: {username} (ID: {uid})\n"
            f"🔧 Услуга: {order.get('service')}\n"
            f"📍 Адрес: {order.get('address')}\n"
            f"🕐 Время: {order.get('time')}\n"
            f"📱 Телефон: {order.get('phone')}"
        )
        return

    # Если не в процессе заказа — напомнить меню
    await update.message.reply_text(
        "Выберите нужный пункт меню 👇",
        reply_markup=MENU
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Ханди запущен (без AI)!")
    app.run_polling()

if __name__ == "__main__":
    main()
