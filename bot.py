import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = 8332704597  # @batumihandy

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

# Состояния пользователей: {uid: {step, service, address, time, phone}}
user_states = {}

async def notify_admin(context, text):
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception as e:
        print(f"Ошибка уведомления: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_states[uid] = {"step": "menu"}
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
        user_states[uid] = {"step": "menu"}

    state = user_states[uid]
    step = state.get("step", "menu")

    # --- КНОПКИ ГЛАВНОГО МЕНЮ ---
    if text == "📋 Услуги":
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
        user_states[uid]["step"] = "menu"
        return

    if text == "📞 Контакты":
        await update.message.reply_text(
            "📞 *Контакты:*\n\n"
            "👤 Алексей\n"
            "📱 +995 593 488 423\n"
            "💬 @HandySolution_Batumi\n\n"
            "Звоните или пишите — ответим быстро!",
            reply_markup=MENU,
            parse_mode="Markdown"
        )
        user_states[uid]["step"] = "menu"
        return

    if text == "💰 Цены":
        await update.message.reply_text(
            "💰 *Цены:*\n\n"
            "Стоимость зависит от объёма работ.\n"
            "Выезд мастера для оценки — *БЕСПЛАТНО*!\n\n"
            "Вызовите мастера и он сразу назовёт цену на месте 👇",
            reply_markup=MENU,
            parse_mode="Markdown"
        )
        user_states[uid]["step"] = "menu"
        return

    if text == "⭐ Оставить отзыв":
        user_states[uid]["step"] = "review"
        await update.message.reply_text(
            "⭐ Напишите ваш отзыв — мы передадим его команде:",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if text == "🔧 Вызвать мастера":
        user_states[uid] = {"step": "ask_service"}
        await update.message.reply_text(
            "Отлично! Давайте оформим заявку.\n\n"
            "1️⃣ *Какая услуга нужна?*",
            reply_markup=SERVICES_KB,
            parse_mode="Markdown"
        )
        return

    # --- ШАГИ ОФОРМЛЕНИЯ ЗАЯВКИ ---
    if step == "ask_service":
        user_states[uid]["service"] = text
        user_states[uid]["step"] = "ask_address"
        await update.message.reply_text(
            f"Услуга: *{text}* ✅\n\n"
            "2️⃣ *Ваш адрес в Батуми?*\n"
            "(улица, номер дома, квартира)",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        return

    if step == "ask_address":
        user_states[uid]["address"] = text
        user_states[uid]["step"] = "ask_time"
        await update.message.reply_text(
            f"Адрес: *{text}* ✅\n\n"
            "3️⃣ *Удобное время для визита мастера?*\n"
            "(например: сегодня после 15:00, завтра утром)",
            parse_mode="Markdown"
        )
        return

    if step == "ask_time":
        user_states[uid]["time"] = text
        user_states[uid]["step"] = "ask_phone"
        await update.message.reply_text(
            f"Время: *{text}* ✅\n\n"
            "4️⃣ *Ваш номер телефона?*\n"
            "(для связи мастера с вами)",
            parse_mode="Markdown"
        )
        return

    if step == "ask_phone":
        user_states[uid]["phone"] = text
        user_states[uid]["step"] = "menu"

        s = user_states[uid]
        order_text = (
            f"🔔 *НОВАЯ ЗАЯВКА!*\n\n"
            f"👤 Клиент: {username}\n"
            f"🔧 Услуга: {s.get('service', '—')}\n"
            f"📍 Адрес: {s.get('address', '—')}\n"
            f"🕐 Время: {s.get('time', '—')}\n"
            f"📱 Телефон: {text}\n"
            f"💬 Telegram ID: {uid}"
        )

        await notify_admin(context, order_text)

        await update.message.reply_text(
            "✅ *Заявка принята!*\n\n"
            f"🔧 Услуга: {s.get('service', '—')}\n"
            f"📍 Адрес: {s.get('address', '—')}\n"
            f"🕐 Время: {s.get('time', '—')}\n"
            f"📱 Телефон: {text}\n\n"
            "Мастер свяжется с вами в ближайшее время!\n\n"
            "По вопросам: @HandySolution_Batumi\n"
            "📞 +995 593 488 423",
            reply_markup=MENU,
            parse_mode="Markdown"
        )
        return

    if step == "review":
        user_states[uid]["step"] = "menu"
        await notify_admin(
            context,
            f"⭐ Отзыв от {username} (ID: {uid}):\n\n{text}"
        )
        await update.message.reply_text(
            "Спасибо за отзыв! ⭐\n"
            "Мы очень ценим ваше мнение!",
            reply_markup=MENU
        )
        return

    # Любое другое сообщение
    await update.message.reply_text(
        "Выберите действие в меню 👇\n"
        "Или позвоните: +995 593 488 423",
        reply_markup=MENU
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Ханди запущен (без Claude API)!")
    app.run_polling()

if __name__ == "__main__":
    main()
