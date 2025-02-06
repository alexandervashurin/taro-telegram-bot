import logging
import random
from datetime import datetime  # Добавьте этот импорт
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters
from opisanie_kart import CARD
from utils import check_subscription, is_admin, send_main_menu
from database import write_user_to_db
from asyncio import Lock

data_lock = Lock()
stats = {
    'total_users': 0,
    'active_users': set(),
    'total_readings': 0,
    'subscriptions': 0
}

async def handle_start(update: Update, context: CallbackContext):
    user = update.effective_user
    async with data_lock:
        stats['total_users'] += 1
        stats['active_users'].add(user.id)

    await send_main_menu(update, context, user.id)

async def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text

    if not await check_subscription(user.id, context.bot):
        await update.message.reply_text(
            "⚠️ Для использования бота необходимо подписаться на канал",
            reply_markup=ReplyKeyboardMarkup(
                [["Проверить подписку"]],
                resize_keyboard=True
            )
        )
        return

    if text == "🎴 Вытянуть карту":
        async with data_lock:
            stats['total_readings'] += 1

        card_name, card_info = random.choice(list(CARD.items()))
        with open(card_info["image"], 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"🔮 {card_name}\n\n{card_info['description']}",
                reply_markup=ReplyKeyboardMarkup(
                    [["🎴 Новый расклад"]],
                    resize_keyboard=True
                )
            )
    elif text == "🎴 Новый расклад":
        await send_main_menu(update, context, user.id)
    elif text == "📊 Статистика":
        await show_stats(update, context)

async def show_stats(update: Update, context: CallbackContext):
    user = update.effective_user
    if not await is_admin(user.id, context.bot):
        await update.message.reply_text("Эта функция доступна только администраторам")
        return

    async with data_lock:
        last_active = datetime.now(tz).strftime("%d.%m.%Y %H:%M")
        stats_text = (
            "📊 Статистика бота:\n\n"
            f"Всего пользователей: {stats['total_users']}\n"
            f"Активных подписчиков: {len(stats['active_users'])}\n"
            f"Всего раскладов: {stats['total_readings']}\n"
            f"Новых подписок: {stats['subscriptions']}\n"
            f"Последняя активность: {last_active}"
        )

    await update.message.reply_text(stats_text)

async def handle_subscription_update(update: Update, context: CallbackContext):
    user = update.effective_user
    subscribed = await check_subscription(user.id, context.bot)

    async with data_lock:
        if subscribed and user.id not in stats['active_users']:
            stats['subscriptions'] += 1
            stats['active_users'].add(user.id)
            write_user_to_db(user.id, user.username)  # Записываем ID подписчика и время в базу данных

    if subscribed:
        await send_main_menu(update, context, user.id)

def setup_handlers(app):
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.ALL, handle_subscription_update), group=1)

