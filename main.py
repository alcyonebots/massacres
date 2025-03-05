from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackContext
import logging
from datetime import datetime, timedelta
import asyncio

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot credentials
API_TOKEN = "8151182853:AAGweMO0CZkaFMZxzYRVoxoC5pbAJHtlXBs"

# Configuration
CHANNEL_ID_1 = -1002033219914  # Invite link channel
CHANNEL_ID_2 = -1001761041493  # Button update channel
MESSAGE_ID = 9  # Message ID in CHANNEL_ID_2
ADMIN_IDS = [6663845789, 1110013191]  # Admins

current_invite_link = None
invite_expiry = 10  # Default expiry in minutes

async def send_log(context: CallbackContext, text: str):
    """Send logs to all admins."""
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, f"**[LOG]** {text}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending log to {admin_id}: {e}")

async def generate_invite_link(context: CallbackContext):
    """Generates and updates the invite link."""
    global current_invite_link
    bot = context.bot

    try:
        chat = await bot.get_chat(CHANNEL_ID_1)
        invite = await bot.create_chat_invite_link(chat_id=CHANNEL_ID_1, expire_date=datetime.utcnow() + timedelta(minutes=invite_expiry))
        current_invite_link = invite.invite_link
        await send_log(context, f"**[New Link]** Valid for {invite_expiry} min: `{current_invite_link}`")

        # Update button
        new_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=current_invite_link)]])
        await bot.edit_message_reply_markup(chat_id=CHANNEL_ID_2, message_id=MESSAGE_ID, reply_markup=new_markup)
        await send_log(context, "**[Updated]** Inline button refreshed.")

    except Exception as e:
        await send_log(context, f"**[Error]** Updating invite link: `{e}`")

async def set_expiry_time(update: Update, context: CallbackContext):
    """Admin command to set invite expiry."""
    global invite_expiry
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("**You are not authorized to use this command.**", parse_mode="Markdown")
        return

    try:
        if len(context.args) != 1:
            await update.message.reply_text("**Invalid format.** Use: `/set 10m` or `/set 1h`", parse_mode="Markdown")
            return

        value = int(context.args[0][:-1])
        unit = context.args[0][-1]

        if unit == "m":
            invite_expiry = value
        elif unit == "h":
            invite_expiry = value * 60
        else:
            await update.message.reply_text("**Invalid unit.** Use 'm' for minutes or 'h' for hours.", parse_mode="Markdown")
            return

        await update.message.reply_text(f"**Invite link expiry set to {invite_expiry} minutes.**", parse_mode="Markdown")
        await send_log(context, f"**[Config]** Admin {update.effective_user.mention_html()} set expiry to {invite_expiry} minutes.")

        await generate_invite_link(context)  # Generate a new link after updating expiry

    except Exception as e:
        await update.message.reply_text("**Error processing your request.**", parse_mode="Markdown")
        await send_log(context, f"**[Error]** Setting expiry time: `{e}`")

async def main():
    """Start the bot."""
    app = Application.builder().token(API_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("set", set_expiry_time))

    # Run the bot
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
