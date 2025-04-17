from telegram.ext import Application
import datetime
import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from workflows.standup import start_stand_up
from services.firestore import get_all_users, get_pending_issues_today
from config import STANDUP_START_TIME, END_NOTIFICATIONS_TIME

async def send_standup_notifications(application: Application) -> None:
    """Ежедневная рассылка уведомлений о начале стендапа."""
    users = get_all_users()
    
    for user in users:
        chat_id = user.get("chat_id")
        user_id = user.get("user_id")
        
        if chat_id and user_id:
            text = start_stand_up({"chat_id": chat_id, "user_id": user_id})
            await application.bot.send_message(
                chat_id=int(chat_id), 
                text=text
            )

async def send_issues_reminders(application: Application) -> None:
    """Проверяет нерешённые проблемы и отправляет напоминания."""
    now_utc = datetime.datetime.now(pytz.utc)
    
    # Не отправляем напоминания после END_NOTIFICATIONS_TIME
    if now_utc.hour > END_NOTIFICATIONS_TIME:
        return
    
    # Получаем все нерешенные проблемы за сегодня
    pending_issues = get_pending_issues_today()
    
    for issue in pending_issues:
        chat_id = issue.get("chat_id")
        
        # Создаем инлайн-клавиатуру для ответа
        keyboard = [[
            InlineKeyboardButton("Yes", callback_data='issue_resolved_yes'),
            InlineKeyboardButton("No", callback_data='issue_resolved_no')
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        msg = f"Did you resolve this issue?\n{issue.get('issue')}"
        
        await application.bot.send_message(
            chat_id=int(chat_id), 
            text=msg, 
            reply_markup=reply_markup
        )

def setup_jobs(application: Application) -> None:
    """Настраивает периодические задачи."""
    # Ежедневное напоминание о стендапе
    application.job_queue.run_daily(
        send_standup_notifications,
        time=datetime.time(hour=STANDUP_START_TIME, minute=0, tzinfo=pytz.utc),
        name="DailyStandupJob"
    )
    
    # Ежечасное напоминание о проблемах
    application.job_queue.run_repeating(
        send_issues_reminders,
        interval=3600,  # 1 час
        first=datetime.datetime.now(pytz.utc).replace(minute=0, second=0),
        name="IssuesReminderJob"
    )