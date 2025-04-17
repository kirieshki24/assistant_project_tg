from bot.dispatcher import setup_application

def main():
    """Основная функция для запуска бота."""
    # Создаем и настраиваем приложение
    application = setup_application()
    
    # Запускаем бота
    print("Starting...")
    application.run_polling()
    print("Stopped")

if __name__ == '__main__':
    main()