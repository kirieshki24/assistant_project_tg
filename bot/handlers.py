from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.firestore import get_context
from workflows.standup import (
    start_stand_up,
    daily_standup_completed_check,
    daily_standup_plans_check,
    daily_standup_ai_response_check,
    handle_issue_yes,
    handle_issue_no,
    handle_issue_resolved,
    handle_issue_not_resolved,
    no_context
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    data = {
        'chat_id': str(update.effective_chat.id),
        'user_id': str(update.effective_user.id)
    }
    await update.message.reply_text(start_stand_up(data))

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    data = {
        'chat_id': str(update.effective_chat.id),
        'user_id': str(update.effective_user.id),
        'message_text': update.message.text
    }

    conversation_context = get_context(data['chat_id'])

    try:
        if conversation_context == "No data found":
            # Если нет записи в Firestore о данном пользователе
            await update.message.reply_text(start_stand_up(data), parse_mode="Markdown")
            return

        last_message_type = conversation_context.get("last_message_type")
        
        if last_message_type == "daily_standup_completed_check":
            await update.message.reply_text(
                daily_standup_completed_check(data), 
                parse_mode="Markdown"
            )
        
        elif last_message_type == "daily_standup_plans_check":
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data='issue_yes'),
                    InlineKeyboardButton("No", callback_data='issue_no'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                daily_standup_plans_check(data),
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        elif last_message_type == "daily_standup_ai_response_check":
            await update.message.reply_text(
                daily_standup_ai_response_check(data), 
                parse_mode="Markdown"
            )
        
        elif last_message_type is None:
            await update.message.reply_text(
                no_context(data), 
                parse_mode="Markdown"
            )
        
    except Exception as e:
        await update.message.reply_text(f"Issue: {str(e)}")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик inline-кнопок."""
    data = {
        'chat_id': str(update.effective_chat.id),
        'user_id': str(update.effective_user.id),
        'action': update.callback_query.data
    }

    try:
        if data['action'] == 'issue_yes':
            await update.callback_query.edit_message_text(
                text=handle_issue_yes(data), 
                parse_mode="Markdown"
            )
        elif data['action'] == 'issue_no':
            await update.callback_query.edit_message_text(
                text=handle_issue_no(data), 
                parse_mode="Markdown"
            )
        elif data['action'] == 'issue_resolved_yes':
            await update.callback_query.edit_message_text(
                text=handle_issue_resolved(data), 
                parse_mode="Markdown"
            )
        elif data['action'] == 'issue_resolved_no':
            await update.callback_query.edit_message_text(
                text=handle_issue_not_resolved(data), 
                parse_mode="Markdown"
            )
    except Exception as e:
        await update.callback_query.edit_message_text(text=f"Issue: {str(e)}")