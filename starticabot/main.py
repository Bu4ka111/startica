from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from handlers import start, message_handler, button_handler
from config import TELEGRAM_TOKEN

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Команда /start
    app.add_handler(CommandHandler("start", start))

    # Обработка нажатий на кнопки ReplyKeyboardMarkup (текстовые кнопки)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Обработка нажатий на inline-кнопки
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
