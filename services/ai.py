from g4f.client import Client
import datetime
import pytz
from services.firestore import get_chat_history, save_chat_history
from config import MAX_CHAT_HISTORY, SYSTEM_PROMPT_PATH

# Инициализация GPT клиента
client = Client()

def load_system_prompt() -> str:
    """Загружает системный промпт из файла."""
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as file:
        return file.read()

def generate_ai_response(prompt: str, user_id: str) -> str:
    """Генерирует ответ с помощью GPT-4o через API."""
    # Получение истории чата из Firestore
    chat_history = get_chat_history(user_id, MAX_CHAT_HISTORY)
    
    # Загрузка системного промпта
    system_prompt = load_system_prompt()
    
    # Формирование сообщений для API
    messages = [{"role": "system", "content": system_prompt}] + chat_history
    messages.append({"role": "user", "content": prompt})
    
    try:
        print("Generating AI response...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            web_search=False
        )
        print("AI response generated")
        response_text = response.choices[0].message.content
        
        # Добавляем новое сообщение в историю чата
        updated_history = chat_history + [
            {"role": "user", "content": prompt},
            {"role": "bot", "content": response_text}
        ]
        
        # Сохраняем обновленную историю
        save_chat_history(user_id, updated_history)
        
        return response_text
    except Exception as e:
        return f"Ошибка: {str(e)}"