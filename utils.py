import logging
from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
from dotenv import load_dotenv
import os
import pytz

load_dotenv()

CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_URL = os.getenv("CHANNEL_URL")
tz = pytz.timezone('Asia/Yekaterinburg')

async def check_subscription(user_id: int, bot: Bot):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        return False

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

