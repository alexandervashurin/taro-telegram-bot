import logging
from dotenv import load_dotenv
import os
from telegram.ext import ApplicationBuilder
from handlers import setup_handlers
from database import create_table

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

API_TOKEN = os.getenv("API_TOKEN")

def main():
    app = ApplicationBuilder().token(API_TOKEN).build()
    setup_handlers(app)
    create_table()
    app.run_polling()

if __name__ == '__main__':
    main()

