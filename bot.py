import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = 8332704597  # @batumihandy

MENU = ReplyKeyboardMarkup([
    [KeyboardButton("🔧 Вызвать мастера"), KeyboardButton("📋 Услуги")],
    [KeyboardButton("💰 Цены"), KeyboardButton("📞 Контакты")],
    [KeyboardButton("🖼 Наши работы"), KeyboardButton("👥 Реферал")],
    [KeyboardButton("⭐ Оставить отзыв")]
], resize_keyboard=True)

SERVICES_KB = ReplyKeyboardMarkup([
    [KeyboardButton("⚡ Электрика"), KeyboardButton("🚿 Сантехника")],
    [KeyboardButton("🏠 Отделка"), KeyboardButton("🪑 Сборка мебели")],
    [KeyboardButton("🚪 Двери"), KeyboardButton("💡 Освещение")],
    [KeyboardButton("🔑 Ремонт под ключ"), KeyboardButton("❓ Другое")]
], resize_keyboard=True)

TIME_KB = ReplyKeyboardMarkup([
    [KeyboardButton("Сегодня утром"), KeyboardButton("Сегодня после 14:00")],
    [KeyboardButton("Завтра утром"), KeyboardButton("Завтра после 14:00")],
    [KeyboardButton("📅 Другой день")]
], resize_keyboard=True)

PHONE_KB = ReplyKeyboardMarkup([
    [KeyboardButton("📱 Отправить мой номер", request_contact=True)]
], resize_keyboard=True, one_time_keyboard=True)

# {uid: {step, service, address, time, phone, order_id}}
user_states = {}

# {order_id: {uid, username, service, address, time, phone, status}}
orders = {}
order_counter = [0]

# Фото работ — вставьте сюда file_id ваших фото после загрузки
WORK_PHOTOS = [
    # "AgACAgIAAxk..." <- сюда вставить file_id фото
]
WORK_PHOTOS_CAPTIONS = [
    "Монтаж электрики",
    "Сантехнические работы",
    "Отделка квартиры",
]

async def notify_admin(context, text, reply_markup=None):
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID, text=text,
            parse_mode="Markdown", reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Ошибка уведомления: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_states[uid] = {"step": "menu"}
    name = update.effective_user.first_name or "друг"

    # Реферальная система — кто пригласил?
    args = context.args
    if args and args[0].startswith("ref"):
        referrer_id = args[0][3:]
        if referrer_id.isdigit() and int(referrer_id) != uid:
            await context.bot.send_message(
                chat_id=int(referrer_id),
                text=f"🎉 По вашей реферальной ссылке зарегистрировался новый пользователь!\n"
                     f"При первом заказе вы получите *скидку 10%* на следующий заказ.",
                parse_mode="Markdown"
            )

    await update.message.reply_text(
        f"Привет, {name}! 👋\n\n"
        "🔧 *HandySolution Batumi*\n"
        "Профессиональный ремонт и монтаж\n\n"
        "✅ Выезд мастера — БЕСПЛАТНО\n"
        "⚡ Выезд в день обращения\n"
        "🏆 Качество гарантировано\n\n"
        "Чем могу помочь?",
        reply_markup=MENU, parse_mode="Markdown"
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # Найти последний заказ клиента
    user_orders = [(oid, o) for oid, o in orders.items() if o["uid"] == uid]
    if not user_orders:
        await update.message.reply_text(
            "У вас пока нет заявок.\nНажмите '🔧 Вызвать мастера' чтобы создать заявку.",
            reply_markup=MENU
        )
        return
    last_id, last_order = sorted(user_orders)[-1]
    status = last_order.get("status", "⏳ Ожидает подтверждения")
    await update.message.reply_text(
        f"📋 *Ваша последняя заявка #{last_id}:*\n\n"
        f"🔧 {last_order['service']}\n"
        f"📍 {last_order['address']}\n"
        f"🕐 {last_order['time']}\n\n"
        f"Статус: {status}",
        reply_markup=MENU, parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("confirm_"):
        order_id = data[8:]
        if order_id in orders:
            orders[order_id]["status"] = "✅ Подтверждена! Мастер едет."
            client_uid = orders[order_id]["uid"]
            try:
                await context.bot.send_message(
                    chat_id=client_uid,
                    text=f"✅ *Ваша заявка #{order_id} подтверждена!*\n\n"
                         f"Мастер скоро свяжется с вами.\n"
                         f"📞 +995 593 488 423",
                    parse_mode="Markdown"
                )
            except:
                pass
            await query.edit_message_text(
                query.message.text + "\n\n✅ *ПОДТВЕРЖДЕНО* — клиент уведомлён",
                parse_mode="Markdown"
            )

    elif data.startswith("cancel_"):
        order_id = data[7:]
        if order_id in orders:
            orders[order_id]["status"] = "❌ Отменена"
            client_uid = orders[order_id]["uid"]
            try:
                await context.bot.send_message(
                    chat_id=client_uid,
                    text=f"❌ К сожалению, заявка #{order_id} отменена.\n\n"
                         f"Позвоните нам: 📞 +995 593 488 423",
                    parse_mode="Markdown"
                )
            except:
                pass
            await query.edit_message_text(
                query.message.text + "\n\n❌ *ОТМЕНЕНО* — клиент уведомлён",
                parse_mode="Markdown"
            )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_states:
        return
    state = user_states[uid]
    if state.get("step") == "ask_phone":
        phone = update.message.contact.phone_number
        await process_phone(update, context, uid, phone)

async def process_phone(update, context, uid, phone):
    user_states[uid]["phone"] = phone
    user_states[uid]["step"] = "menu"
    s = user_states[uid]
    username = update.effective_user.first_name or "Клиент"

    order_counter[0] += 1
    order_id = str(order_counter[0])
    orders[order_id] = {
        "uid": uid,
        "username": username,
        "service": s.get("service", "—"),
        "address": s.get("address", "—"),
        "time": s.get("time", "—"),
        "phone": phone,
        "status": "⏳ Ожидает подтверждения"
    }

    admin_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"confirm_{order_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{order_id}")
        ]
    ])

    order_text = (
        f"🔔 *НОВАЯ ЗАЯВКА #{order_id}!*\n\n"
        f"👤 {username} (ID: {uid})\n"
        f"🔧 Услуга: {s.get('service','—')}\n"
        f"📍 Адрес: {s.get('address','—')}\n"
        f"🕐 Время: {s.get('time','—')}\n"
        f"📱 Телефон: {phone}"
    )
    await notify_admin(context, order_text, reply_markup=admin_kb)

    await update.message.reply_text(
        f"✅ *Заявка #{order_id} принята!*\n\n"
        f"🔧 {s.get('service','—')}\n"
        f"📍 {s.get('address','—')}\n"
        f"🕐 {s.get('time','—')}\n"
        f"📱 {phone}\n\n"
        "Ожидайте подтверждения от мастера!\n"
        "Написать /статус чтобы проверить статус заявки.",
        reply_markup=MENU, parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    username = update.effective_user.first_name or "Клиент"

    if uid not in user_states:
        user_states[uid] = {"step": "menu"}

    state = user_states[uid]
    step = state.get("step", "menu")

    if text == "📋 Услуги":
        user_states[uid]["step"] = "menu"
        await update.message.reply_text(
            "📋 *Наши услуги:*\n\n"
            "⚡ Электрика\n🚿 Сантехника\n🏠 Отделка\n"
            "🪑 Сборка мебели\n🚪 Установка дверей\n"
            "💡 Освещение\n🔑 Ремонт под ключ\n\n"
            "Выезд для оценки — БЕСПЛАТНО!",
            reply_markup=MENU, parse_mode="Markdown"
        )
        return

    if text == "📞 Контакты":
        user_states[uid]["step"] = "menu"
        await update.message.reply_text(
            "📞 *Контакты:*\n\n👤 Алексей\n📱 +995 593 488 423\n💬 @HandySolution_Batumi",
            reply_markup=MENU, parse_mode="Markdown"
        )
        return

    if text == "💰 Цены":
        user_states[uid]["step"] = "menu"
        await update.message.reply_text(
            "💰 *Цены:*\n\nСтоимость зависит от объёма работ.\n"
            "Выезд мастера для оценки — *БЕСПЛАТНО*!\n\n"
            "Вызовите мастера — он назовёт цену на месте 👇",
            reply_markup=MENU, parse_mode="Markdown"
        )
        return

    if text == "⭐ Оставить отзыв":
        user_states[uid]["step"] = "review"
        await update.message.reply_text(
            "⭐ Напишите ваш отзыв:", reply_markup=ReplyKeyboardRemove()
        )
        return

    if text == "👥 Реферал":
        user_states[uid]["step"] = "menu"
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref{uid}"
        await update.message.reply_text(
            "👥 *Реферальная программа*\n\n"
            "Поделитесь ссылкой с друзьями!\n"
            "Когда друг сделает заказ — вы получите *скидку 10%* на следующий заказ.\n\n"
            f"Ваша ссылка:\n`{ref_link}`",
            reply_markup=MENU, parse_mode="Markdown"
        )
        return

    if text == "🖼 Наши работы":
        user_states[uid]["step"] = "menu"
        if WORK_PHOTOS:
            for i, photo_id in enumerate(WORK_PHOTOS):
                caption = WORK_PHOTOS_CAPTIONS[i] if i < len(WORK_PHOTOS_CAPTIONS) else ""
                await context.bot.send_photo(
                    chat_id=uid, photo=photo_id, caption=caption
                )
        else:
            await update.message.reply_text(
                "📸 Фото наших работ скоро появятся здесь!\n\n"
                "Пока можете посмотреть отзывы клиентов или вызвать мастера.",
                reply_markup=MENU
            )
        return

    if text == "🔧 Вызвать мастера":
        user_states[uid] = {"step": "ask_service"}
        await update.message.reply_text(
            "Оформляем заявку!\n\n1️⃣ *Какая услуга нужна?*",
            reply_markup=SERVICES_KB, parse_mode="Markdown"
        )
        return

    if step == "ask_service":
        user_states[uid]["service"] = text
        user_states[uid]["step"] = "ask_address"
        await update.message.reply_text(
            f"Услуга: *{text}* ✅\n\n2️⃣ *Ваш адрес в Батуми?*\n(улица, дом, квартира)",
            reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown"
        )
        return

    if step == "ask_address":
        user_states[uid]["address"] = text
        user_states[uid]["step"] = "ask_time"
        await update.message.reply_text(
            f"Адрес записан ✅\n\n3️⃣ *Удобное время для визита мастера?*",
            reply_markup=TIME_KB, parse_mode="Markdown"
        )
        return

    if step == "ask_time":
        user_states[uid]["time"] = text
        user_states[uid]["step"] = "ask_phone"
        await update.message.reply_text(
            f"Время записано ✅\n\n4️⃣ *Ваш номер телефона?*\n"
            "Нажмите кнопку или введите вручную:",
            reply_markup=PHONE_KB, parse_mode="Markdown"
        )
        return

    if step == "ask_phone":
        await process_phone(update, context, uid, text)
        return

    if step == "review":
        user_states[uid]["step"] = "menu"
        await notify_admin(context, f"⭐ Отзыв от {username} (ID: {uid}):\n\n{text}")
        await update.message.reply_text(
            "Спасибо за отзыв! ⭐", reply_markup=MENU
        )
        return

    await update.message.reply_text(
        "Выберите действие в меню 👇", reply_markup=MENU
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("статус", cmd_status))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Ханди запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
