"""Conversation handlers for the Quote Bot's onboarding flow."""
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ConversationHandler, 
    MessageHandler, 
    CommandHandler, 
    filters, 
    ContextTypes
)

from quote_bot.db import save_user_preferences

logger = logging.getLogger(__name__)

# Conversation states
TOPIC, TONE, QUOTE_LENGTH, AUTHOR_PREF, DELIVERY_TIME, WEEKEND_TOGGLE, CONTEXT_LINE = range(7)

# --- Helper Functions ---

def get_topics_keyboard():
    """Get the keyboard for topic selection."""
    return [
        ["Startup grit", "Investment Wisdom"],
        ["Productivity", "Entrepreneurship"],
        ["Creativity", "Mindfulness"],
        ["Done"]
    ]

def get_tone_keyboard():
    """Get the keyboard for tone selection."""
    return [["Motivational", "Educational"], ["Humorous", "Philosophical"]]

def get_quote_length_keyboard():
    """Get the keyboard for quote length selection."""
    return [["Short (< 10 words)", "Medium (10-15 words)", "Long >20 words"]]

def get_delivery_time_keyboard():
    """Get the keyboard for delivery time selection."""
    return [
        ["06:00", "07:00", "08:00"],
        ["18:00", "19:00", "20:00"]
    ]

# --- Conversation Handlers ---

async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the onboarding conversation."""
    context.user_data['topics'] = []
    
    await update.message.reply_text(
        "Welcome! Let's personalize your daily quotes.\n\n"
        "Which themes interest you most? (choose up to 3, then tap 'Done')",
        reply_markup=ReplyKeyboardMarkup(
            get_topics_keyboard(),
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return TOPIC

async def handle_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle topic selection."""
    text = update.message.text
    
    if text == 'Done':
        if not context.user_data.get('topics'):
            await update.message.reply_text(
                "Please select at least one topic or type 'Done' to skip."
            )
            return TOPIC
        
        # Move to tone selection
        await update.message.reply_text(
            "What tone do you prefer for your quotes?",
            reply_markup=ReplyKeyboardMarkup(
                get_tone_keyboard(),
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return TONE
    
    # Add topic if not already selected and not exceeding limit
    if len(context.user_data['topics']) < 3 and text not in context.user_data['topics']:
        context.user_data['topics'].append(text)
        
    # Show current selection
    if context.user_data['topics']:
        await update.message.reply_text(
            f"Selected topics: {', '.join(context.user_data['topics'])}\n\n"
            "Select more topics or tap 'Done' to continue.",
            reply_markup=ReplyKeyboardMarkup(
                get_topics_keyboard(),
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
    
    return TOPIC

async def handle_tone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tone selection."""
    context.user_data['tone'] = update.message.text
    
    await update.message.reply_text(
        "What length of quotes do you prefer?",
        reply_markup=ReplyKeyboardMarkup(
            get_quote_length_keyboard(),
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return QUOTE_LENGTH

async def handle_quote_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quote length selection."""
    context.user_data['quote_length'] = update.message.text
    await update.message.reply_text(
        "Do you have a favorite author or thinker? (Type 'Skip' if not)",
        reply_markup=ReplyKeyboardRemove()
    )
    return AUTHOR_PREF

async def handle_author_pref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle author preference input."""
    if update.message.text.lower() != 'skip':
        context.user_data['author_pref'] = update.message.text
    
    await update.message.reply_text(
        "When would you like to receive your daily quote?",
        reply_markup=ReplyKeyboardMarkup(
            get_delivery_time_keyboard(),
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return DELIVERY_TIME

async def handle_delivery_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delivery time selection."""
    context.user_data['delivery_time'] = update.message.text
    
    keyboard = [["Yes", "No"]]
    await update.message.reply_text(
        "Would you like to receive quotes on weekends?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return WEEKEND_TOGGLE

async def handle_weekend_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle weekend toggle selection."""
    context.user_data['weekend_toggle'] = update.message.text.lower() == 'yes'
    
    keyboard = [["Yes, add takeaway", "No, quote only"]]
    await update.message.reply_text(
        "Would you like a one-line takeaway under each quote?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return CONTEXT_LINE

async def onboarding_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete the onboarding process and save preferences."""
    context.user_data['context_line'] = update.message.text == 'Yes, add takeaway'
    
    # Save preferences to database
    user_id = update.effective_user.id
    save_user_preferences(user_id, context.user_data)
    
    await update.message.reply_text(
        "🎉 All set! Your preferences have been saved.\n\n"
        "You'll start receiving your personalized quotes soon.\n"
        "Use /status to check your preferences or /help for more options.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Clear conversation data
    context.user_data.clear()
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current conversation."""
    await update.message.reply_text(
        'Onboarding cancelled. You can start again with /onboard.',
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

def setup_conversation_handlers(application):
    """Set up the conversation handler for onboarding."""
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('onboard', start_onboarding)],
        states={
            TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topic)],
            TONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tone)],
            QUOTE_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quote_length)],
            AUTHOR_PREF: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_author_pref)],
            DELIVERY_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delivery_time)],
            WEEKEND_TOGGLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_weekend_toggle)],
            CONTEXT_LINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_complete)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    logger.info("Conversation handlers have been set up")
