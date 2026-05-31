import os
import anthropic
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ADMIN_ID = 8332704597  # @batumihandy

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Ты Ханди, помощник HandySolution Batumi.
Услуги: электрика, сантехника, отделка, мебель, двери, освещение, ремонт под ключ.
Контакт: @HandySolution_Batumi, +995 593 488 423, Алексей.
Выезд для оценки бесплатный. Работаем в Батуми.
Когда клиент хочет вызвать мастера — собери: тип услуги, адрес, удобное время, телефон.
Отвечай коротко и по делу на языке клиента."""

user_histories = {}

MENU = ReplyKeyboardMarkup([
    [KeyboardButton("🔧 Вызвать мастера"), KeyboardButton("📋 Услуги")],
    [KeyboardButton("💰 Цены"), KeyboardButton("📞 Контакты")],
    [KeyboardButton("⭐ Оставить отзыв")]
], resize_keyboard=True)

async def notify_admin(context, text):
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception as e:
        print(f"Ошибка уведомления админа: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_histories[uid] = []
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

    if uid not in user_histories:
        user_histories[uid] = []

    # Обработка кнопок меню
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
        return

    if text == "💰 Цены":
        await update.message.reply_text(
            "💰 *Цены:*\n\n"
            "Стоимость зависит от объёма работ.\n"
            "Выезд мастера для оценки — *БЕСПЛАТНО*!\n\n"
            "Напишите что нужно сделать — дам примерную стоимость 👇",
            reply_markup=MENU,
            parse_mode="Markdown"
        )
        return

    if text == "🔧 Вызвать мастера":
        await update.message.reply_text(
            "Отлично! Чтобы вызвать мастера, скажите:\n\n"
            "1️⃣ Какая услуга нужна?\n"
            "2️⃣ Ваш адрес в Батуми?\n"
            "3️⃣ Удобное время?\n"
            "4️⃣ Ваш номер телефона?\n\n"
            "Можете написать всё сразу 👇",
            reply_markup=MENU
        )
        return

    if text == "⭐ Оставить отзыв":
        await update.message.reply_text(
            "Спасибо, что выбрали нас! ⭐\n\n"
            "Напишите ваш отзыв — мы передадим его команде.\n"
            "Это помогает нам становиться лучше!",
            reply_markup=MENU
        )
        return

    # Передаём в Claude для умного ответа
    user_histories[uid].append({"role": "user", "content": text})
    if len(user_histories[uid]) > 20:
        user_histories[uid] = user_histories[uid][-20:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        r = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=user_histories[uid]
        )
        reply = r.content[0].text
    except Exception as e:
        print(f"Claude error: {e}")
        reply = "Позвоните напрямую: +995 593 488 423 (Алексей)"

    user_histories[uid].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply, reply_markup=MENU)

    # Уведомляем админа если клиент хочет заказать
    keywords = ["адрес", "улиц", "позвон", "телефон", "приедьт", "вызов", "заявк", "когда"]
    if any(kw in text.lower() for kw in keywords):
        await notify_admin(
            context,
            f"🔔 Новый клиент!\n"
            f"👤 {username} (ID: {uid})\n"
            f"💬 {text}\n"
            f"🤖 Ответ бота: {reply}"
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Ханди запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
