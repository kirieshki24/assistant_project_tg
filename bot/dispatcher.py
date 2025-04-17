from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from bot.handlers import start_command, handle_text_message, handle_callback_query
from bot.jobs import setup_jobs
from config import BOT_TOKEN

def setup_application() -> Application:
    """Настраивает и возвращает экземпляр приложения Telegram."""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    
    # Регистрируем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Регистрируем обработчик callback-запросов
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Настраиваем периодические задачи
    setup_jobs(application)
    
    return application