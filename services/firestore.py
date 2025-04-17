from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter
import datetime
import pytz
import os
from config import GOOGLE_CREDENTIALS_PATH

# Установка переменной окружения до инициализации клиента
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDENTIALS_PATH

# Инициализация Firestore
db = firestore.Client()

def get_context(chat_id: str) -> dict:
    """Получает контекст чата из Firestore по ID чата."""
    doc_ref = db.collection("conversation_context").document(chat_id)
    doc = doc_ref.get()
    if not doc.exists:
        return "No data found"
    return doc.to_dict()

def save_standup(user_id: str, completed=None, plans=None, issues=None) -> None:
    """Сохраняет или обновляет ежедневный отчёт в Firestore."""
    if not completed and not plans and not issues:
        doc_ref = db.collection("stand_up_history").document(datetime.datetime.now().strftime("%Y-%m-%d") + ' ' + user_id)
        doc_ref.set({
            "user_id": user_id,
            "timestamp": datetime.datetime.now(),
            "completed": completed,
            "plans": plans,
            "issues": issues
        })
    else:
        doc_id = datetime.datetime.now().strftime("%Y-%m-%d") + ' ' + user_id
        updates = {}
        
        if completed is not None:
            updates["completed"] = completed
        if plans is not None:
            updates["plans"] = plans
        if issues is not None:
            updates["issues"] = issues
        
        if updates:
            db.collection("stand_up_history").document(doc_id).update(updates)

def update_context(chat_id: str, message_type: str, user_id: str) -> None:
    """Обновляет контекст диалога в Firestore."""
    doc_ref = db.collection("conversation_context").document(chat_id)
    doc_ref.set({
        "last_message_type": message_type,
        "user_id": user_id,
        "timestamp": datetime.datetime.now()
    })

def save_issue(chat_id: str, issue: str, status: str, user_id: str) -> None:
    """Сохраняет информацию о проблеме в отдельную коллекцию Firestore."""
    doc_ref = db.collection("issues").document()
    doc_ref.set({
        "issue": issue,
        "status": status,
        "user_id": user_id,
        "chat_id": chat_id,
        "timestamp": datetime.datetime.now(pytz.utc)
    })

def get_chat_history(user_id: str, limit: int) -> list:
    """Получает историю чата для пользователя."""
    chat_history_ref = db.collection("chat_history").document(user_id)
    chat_history_doc = chat_history_ref.get()
    chat_history = []

    if chat_history_doc.exists and chat_history_doc.to_dict().get("timestamp") >= datetime.datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0):
        chat_history = chat_history_doc.to_dict().get("history", [])
    
    return chat_history[-limit:]  # Ограничиваем количеством сообщений

def save_chat_history(user_id: str, chat_history: list) -> None:
    """Сохраняет историю чата для пользователя."""
    chat_history_ref = db.collection("chat_history").document(user_id)
    chat_history_ref.set({"history": chat_history, "timestamp": datetime.datetime.now(pytz.utc)})

def update_issue_status(user_id: str, status: str) -> None:
    """Обновляет статус последней pending-проблемы пользователя."""
    latest_pending_issue = (
        db.collection("issues")
        .where(filter=FieldFilter("user_id", "==", user_id))
        .where(filter=FieldFilter("status", "==", "Pending"))
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )
    for doc in latest_pending_issue:
        db.collection("issues").document(doc.id).update({"status": status})
        break

def get_pending_issues_today() -> list:
    """Получает все нерешенные проблемы за сегодня."""
    now_utc = datetime.datetime.now(pytz.utc)
    start_of_day = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    
    issues = []
    issues_ref = (
        db.collection("issues")
        .where(filter=FieldFilter("status", "==", "Pending"))
        .where(filter=FieldFilter("timestamp", ">=", start_of_day))
        .stream()
    )
    
    for issue_doc in issues_ref:
        issue_data = issue_doc.to_dict()
        issue_data['id'] = issue_doc.id
        issues.append(issue_data)
    
    return issues

def get_all_users() -> list:
    """Получает список всех пользователей с активным контекстом."""
    users = []
    users_docs = db.collection("conversation_context").stream()
    
    for doc in users_docs:
        users.append(doc.to_dict())
    
    return users