"""Command handlers for the Quote Bot."""
import asyncio
import logging
import re
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
from quote_bot.db.user_repository import record_daily_interaction, get_streak_badge
from quote_bot.db.user_repository import get_user_prefs 
from bot.services.ai_service import ai_service
from bot.services import quote_service
from bot.utils.helpers import escape_markdown, format_quote
from bot.handlers.callbacks import get_quote_keyboard
from quote_bot.db.interaction_repository import get_quotes_by_interaction, get_quote_interaction
from quote_bot.db.quote_repository import get_quote_by_id
from quote_bot.db.user_repository import get_user, update_user_status, add_user

logger = logging.getLogger(__name__)

async def _maybe_send_streak(update: Update, user_id: int) -> None:
    """If this is the first interaction today, bump/reset and send their streak badge."""
    try:
        streak = record_daily_interaction(user_id)
        if streak:
            badge = get_streak_badge(streak)
            msg = f"🔥 You’ve used me {streak} day{'s' if streak > 1 else ''} in a row!"
            if badge:
                msg += f" Badge unlocked: {badge}."
            await update.message.reply_text(msg)
    except Exception:
        logger.exception("Failed to record daily streak")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    add_user(user.id)
    
    await update.message.reply_text(
        f"Hi {user.first_name}! I'm your Quote Bot.\n\n"
        "I'll send you inspiring quotes daily. Here's what you can do:\n"
        "• /random - Get a random quote now\n"
        "• /generate - Generates a quote based on preferences inputted in onboarding form\n"
        "• /quote topic - Shows 3 quotes related to chosen topic: eg. confidence or resilience\n"
        "• /author author name - Shows 5 quotes by desired author\n"
        "• /onboard - Set your preferences\n"
        "• /pause - Pause daily quotes\n"
        "• /resume - Resume daily quotes\n"
        "• /status - Check your current settings\n"
        "• /help - Show this help message"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    help_text = (
        "🤖 *Quote Bot Help*\n\n"
        "*Commands:*\n"
        "• /start - Start the bot and see welcome message\n"
        "• /random - Get a random quote now\n"
        "• /onboard - Set your preferences\n"
        "• /pause - Pause daily quotes\n"
        "• /resume - Resume daily quotes\n"
        "• /status - Check your current settings\n"
        "• /help - Show this help message\n"
        "• /liked - Show your list of liked quotes\n"
        "• /disliked - Show your list of disliked quotes\n"
        "• /author author name - Shows 5 quotes by desired author\n"
        "• /quote topic - Shows 3 quotes related to chosen topic: eg. confidence or resilience\n\n"
        "*Interactive Buttons:*\n"
        "• 👍 - Like a quote\n"
        "• 👎 - Dislike a quote\n"
        "• 🔄 - Get another quote"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def random_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /random command."""
    user_id = update.effective_user.id
    
    prefs = get_user_prefs(user_id) or {}
    prefs['is_active'] = not get_user(user_id).is_paused
    quote_data = quote_service.get_quote_for_user(user_id, prefs)
    
    
    if not quote_data:
        return await update.message.reply_text("I couldn't find a suitable quote for you right now. Try again later!")
        
    # Format the quote with proper escaping
    quote = escape_markdown(quote_data.get("quote", ""))
    author = escape_markdown(quote_data.get("author", ""))
    takeaway = escape_markdown(quote_data.get("takeaway", ""))
        
    # Build the message with HTML formatting
    message_text = f'<i>"{quote}"</i>'
    if author:
        message_text += f'<i>\n\n- {author}</i>'
    if prefs.get("context_line", 1) and takeaway:
        message_text += f'\n\n💡 <b>Takeaway:</b> {takeaway}'
        
    # Get the keyboard with like/dislike/favorite buttons
    keyboard = get_quote_keyboard(quote_data['id'], user_id)
        
    # Send the quote with HTML parsing
    await update.message.reply_text(
        message_text,
        reply_markup=keyboard,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

    await _maybe_send_streak(update, user_id)

async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /pause command."""
    user_id = update.effective_user.id
    update_user_status(user_id, is_paused=True)
    
    await update.message.reply_text(
        "⏸️ You've paused your daily quotes. Use /resume to start receiving them again."
    )

async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /resume command."""
    user_id = update.effective_user.id
    update_user_status(user_id, is_paused=False)
    
    await update.message.reply_text(
        "▶️ You've resumed your daily quotes. You'll receive your next quote as scheduled."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /status command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    if user:
        prefs = {
            'is_active': not user.is_paused,
            'preferred_time': getattr(user, 'preferred_time', None),
            'timezone': getattr(user, 'timezone', None),
        }
    else:
        prefs = {}
    
    status_text = (
        f"📊 <b>Your Preferences</b>\n"
        f"• Daily Quotes: {'✅ Enabled' if prefs['is_active'] else '❌ Disabled'}\n"
        f"• Preferred Time: {prefs['preferred_time'] or 'Not set'}\n"
        f"• Timezone: {prefs['timezone'] or 'Not set'}\n\n"
        "Use /pause to pause daily quotes\n"
        "Use /resume to resume daily quotes\n"
        "Use /help to see all available commands"
    )
    
    await update.message.reply_text(status_text, parse_mode='HTML')

async def show_liked_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /liked command to show all liked quotes (stripping out takeaways)."""
    user_id = update.effective_user.id
    rows = get_quotes_by_interaction(user_id, 'liked')
    if not rows:
        await update.message.reply_text(
            "You haven't liked any quotes yet. Use the 👍 button to like quotes!"
        )
        return

    header = "<b>❤️ Your Liked Quotes:</b>\n\n"
    continued = "<b>❤️ Your Liked Quotes (continued):</b>\n\n"

    # Build clean entries (strip off any "Takeaway:" + trailing text)
    entries = []
    for idx, row in enumerate(rows, 1):
        clean = re.split(r'(?i)takeaway:', row['quote'])[0].strip()
        entries.append(
            f"{idx}. <i>\"{escape_markdown(clean)}\"</i>\n— <b>{escape_markdown(row.get('author','Unknown'))}</b>"
        )

    # Send in chunks of 5 entries
    CHUNK = 5
    for start in range(0, len(entries), CHUNK):
        chunk = entries[start : start + CHUNK]
        prefix = header if start == 0 else continued
        await update.message.reply_text(
            prefix + "\n\n".join(chunk),
            parse_mode='HTML',
            disable_web_page_preview=True
        )

async def show_disliked_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /disliked command to show all disliked quotes (stripping out takeaways)."""
    user_id = update.effective_user.id
    rows = get_quotes_by_interaction(user_id, 'disliked')
    if not rows:
        await update.message.reply_text(
            "You haven't disliked any quotes yet. Use the 👎 button to dislike quotes."
        )
        return

    header = "<b>👎 Your Disliked Quotes:</b>\n\n"
    continued_header = "<b>👎 Your Disliked Quotes (continued):</b>\n\n"

    # Build clean entries (strip off any "Takeaway:" + trailing text)
    entries = []
    for idx, row in enumerate(rows, 1):
        clean = re.split(r'(?i)takeaway:', row['quote'])[0].strip()
        entries.append(
            f"{idx}. <i>\"{escape_markdown(clean)}\"</i>\n— <b>{escape_markdown(row.get('author', 'Unknown'))}</b>"
        )

    # Send in chunks of N entries
    CHUNK = 5
    for start in range(0, len(entries), CHUNK):
        chunk = entries[start : start + CHUNK]
        prefix = header if start == 0 else continued_header
        await update.message.reply_text(
            prefix + "\n\n".join(chunk),
            parse_mode='HTML',
            disable_web_page_preview=True
        )

async def generate_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate an AI‐crafted quote with a one-line takeaway, cleanly formatted."""
    user_id = update.effective_user.id
    
    prefs = get_user_prefs(user_id)
    if not prefs:
        return await update.message.reply_text("I don’t have your preferences yet. Please run /onboard first 😊")

    raw = await ai_service.generate_quote(user_id, prefs)
    if not raw or raw.strip().upper() == "RETRY":
        return await update.message.reply_text("Sorry, I couldn’t craft a good quote right now — try again!")


    # split into non-empty lines
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    def strip_number(l): return re.sub(r'^\s*\d+[\)\.\-]?\s*','',l).strip()

    # 1) quote text
    quote_line = strip_number(lines[0]).strip('"')
    author     = strip_number(lines[1]).lstrip('- ') if len(lines)>1 else "Unknown"
    takeaway   = ""

    if len(lines)>2:
        tk = strip_number(lines[2])
        takeaway = re.sub(r'(?i)^takeaway:\s*','',tk).strip()

    # Build your HTML-formatted message
    msg = (
        f'<i>"{escape_markdown(quote_line)}"</i>\n'
        f'<i>- {escape_markdown(author)}</i>'
    )
    # only if they want it
    if prefs.get("context_line",1) and takeaway:
        msg += f'\n\n<b>🔍 Takeaway:</b> {escape_markdown(takeaway)}'

    # send with keyboard
    quote_id = -int(asyncio.get_event_loop().time()*1000)
    keyboard = get_quote_keyboard(quote_id, user_id)
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=keyboard)

    # show streak once per day
    await _maybe_send_streak(update, user_id)

async def author_deep_dive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `/author <name>` → returns 5 quotes by that author via AI."""
    # parse the author name from the command args
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /author <Author Name>")
        return
    author = " ".join(args)
    await update.message.reply_text(f"🔎 Looking up quotes by *{author}*…", parse_mode="Markdown")
    
    quotes = await ai_service.deep_dive_by_author(author, count=5)
    if not quotes:
        await update.message.reply_text(
            f"Sorry, I couldn’t fetch quotes by {author} right now."
        )
        return
    
    # send each quote as a numbered list
    text = "\n\n".join(f"{i+1}. {q}" for i, q in enumerate(quotes))
    await update.message.reply_text(text, parse_mode="Markdown")

async def quote_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `/quote <topic>` → returns 3 fitting quotes via AI."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /quote <topic>\nE.g. /quote resilience")
        return
    
    topic = " ".join(args)
    await update.message.reply_text(f"🔎 Fetching quotes about *{topic}*…", parse_mode="Markdown")
    quotes = await ai_service.generate_by_topic(topic, count=3)

    if not quotes:
        return await update.message.reply_text(
            f"Sorry, I couldn’t find quotes on '{topic}' right now."
        )
    
    out = "\n\n".join(f"{i+1}. {q}" for i, q in enumerate(quotes))
    await update.message.reply_text(out, parse_mode="Markdown")

def setup_command_handlers(application: Application) -> None:
    """Set up all command handlers."""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("random", random_quote))
    application.add_handler(CommandHandler("pause", pause))
    application.add_handler(CommandHandler("generate", generate_quote))
    application.add_handler(CommandHandler("resume", resume))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("liked", show_liked_quotes))
    application.add_handler(CommandHandler("disliked", show_disliked_quotes))
    application.add_handler(CommandHandler("author", author_deep_dive))
    application.add_handler(CommandHandler("quote", quote_topic))
    
    logger.info("Command handlers have been set up")
    logger.info("Added /author deep-dive handler")
