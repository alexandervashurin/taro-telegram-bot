import logging
import random
from telegram import Bot, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from opisanie_kart import CARD
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz
from asyncio import Lock

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

API_TOKEN = os.getenv("API_TOKEN")          # токен можно получить у BotFather
CHANNEL_ID = os.getenv("CHANNEL_ID")        # можно получить переслав любое сообщение из Вашего канала в этот бот https://t.me/getmyid_bot
CHANNEL = os.getenv("CHANNEL")              # название Вашего канала
CHANNEL_URL = os.getenv("CHANNEL_URL")      # адрес канала
SUBSCRIBERS_FILE = "subscribers.txt"       # файл для записи ID подписчиков

# Глобальные состояния
user_states = {}
stats = {
    'total_users': 0,
    'active_users': set(),
    'total_readings': 0,
    'subscriptions': 0
}
data_lock = Lock()
tz = pytz.timezone('Asia/Yekaterinburg')

# Функция для записи ID подписчиков в файл
def write_subscriber_id(user_id: int):
    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    with open(SUBSCRIBERS_FILE, 'a') as file:
        file.write(f"{user_id}, {current_time}\n")

# проверка пользователя на подписку на Ваш телеграм-канал
async def check_subscription(user_id: int, bot: Bot):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        return False

# проверка пользователя на то является ли он администратором телеграм-канала
async def is_admin(user_id: int, bot: Bot):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['administrator', 'creator']
    except Exception as e:
        logging.error(f"Admin check error: {e}")
        return False

async def send_main_menu(update: Update, context: CallbackContext, user_id: int):
    is_admin_user = await is_admin(user_id, context.bot)
    subscribed = await check_subscription(user_id, context.bot)

    if subscribed:
        text = "Спасибо за подписку! 🙏\nВыберите действие:"
        buttons = [["🎴 Вытянуть карту"]]
        if is_admin_user:
            buttons.append(["📊 Статистика"])
    else:
        text = f"🔮 Чтобы получить бесплатный расклад, подпишитесь на наш канал: {CHANNEL_URL}"
        buttons = [["Проверить подписку"]]

    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True, input_field_placeholder="Выберите действие")
    await update.message.reply_text(text, reply_markup=keyboard)

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
            write_subscriber_id(user.id)  # Записываем ID подписчика и время в файл

    if subscribed:
        await send_main_menu(update, context, user.id)

def main():
    app = ApplicationBuilder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    app.add_handler(MessageHandler(
        filters.ALL,
        handle_subscription_update
    ), group=1)

    app.run_polling()

if __name__ == '__main__':
    main()
