import telebot
from celery import shared_task

from library_service_api import settings

BOT_TOKEN = settings.TG_BOT_TOKEN
CHAT_ID = settings.TG_CHAT_ID


@shared_task
def send_telegram_message(message):
    bot = telebot.TeleBot(BOT_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=message)
