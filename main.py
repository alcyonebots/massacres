import logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters
from telegram.error import TelegramError

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot credentials
API_TOKEN = "8151182853:AAGweMO0CZkaFMZxzYRVoxoC5pbAJHtlXBs"

# Configuration
CHANNEL_ID_1 = -1002033219914  # Channel where invite is generated
CHANNEL_ID_2 = -1001761041493  # Channel where button is updated
MESSAGE_ID = 9  # Fixed message ID in CHANNEL_ID_2
ADMIN_IDS = [6663845789, 1110013191]  # List of admin IDs

current_invite_link = None
invite_expiry = 10  # Default expiry time in minutes


def send_log(context: CallbackContext, text: str):
    """Send logs to all admins."""
    for admin_id in ADMIN_IDS:
        try:
            context.bot.send_message(admin_id, f"**[LOG]** {text}", parse_mode="Markdown")
        except TelegramError as e:
            logger.error(f"Error sending log to {admin_id}: {e}")


def generate_invite_link(context: CallbackContext):
    """Generates a new invite link and updates the button."""
    global current_invite_link

    try:
        # Revoke all existing invite links
        links = context.bot.get_chat_invite_links(CHANNEL_ID_1, invite_link=True)
        for link in links:
            if not link.is_revoked:
                context.bot.revoke_chat_invite_link(CHANNEL_ID_1, link.invite_link)
                send_log(context, f"**[Revoked]** Invite link: `{link.invite_link}`")

        # Create a new invite link
        expire_date = datetime.utcnow() + timedelta(minutes=invite_expiry)
        invite = context.bot.create_chat_invite_link(CHANNEL_ID_1, expire_date=expire_date)
        current_invite_link = invite.invite_link
        send_log(context, f"**[New Link]** Valid for **{invite_expiry} min**: `{current_invite_link}`")

        # Update the inline button in the fixed message
        new_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=current_invite_link)]])
        context.bot.edit_message_reply_markup(CHANNEL_ID_2, MESSAGE_ID, reply_markup=new_markup)
        send_log(context, "**[Updated]** Inline button refreshed.")

    except TelegramError as e:
        send_log(context, f"**[Error]** Updating invite link: `{e}`")


def set_expiry_time(update: Update, context: CallbackContext):
    """Allows admins to set the invite link expiry time dynamically."""
    global invite_expiry
    user_id = update.message.from_user.id

    if user_id not in ADMIN_IDS:
        update.message.reply_text("**You are not authorized to use this command.**", parse_mode="Markdown")
        return

    try:
        if len(context.args) != 1:
            update.message.reply_text("**Invalid format.** Use: `/set 10m` or `/set 1h`", parse_mode="Markdown")
            return

        value = int(context.args[0][:-1])
        unit = context.args[0][-1]

        if unit == "m":
            invite_expiry = value
        elif unit == "h":
            invite_expiry = value * 60
        else:
            update.message.reply_text("**Invalid unit.** Use 'm' for minutes or 'h' for hours.", parse_mode="Markdown")
            return

        update.message.reply_text(f"**Invite link expiry set to {invite_expiry} minutes.**", parse_mode="Markdown")
        send_log(context, f"**[Config]** Admin [{update.message.from_user.full_name}](tg://user?id={user_id}) set expiry to **{invite_expiry} minutes.**")

        generate_invite_link(context)  # Generate a new link immediately after changing expiry

    except Exception as e:
        update.message.reply_text("**Error processing your request.**", parse_mode="Markdown")
        send_log(context, f"**[Error]** Setting expiry time: `{e}`")


def on_new_member(update: Update, context: CallbackContext):
    """Resets the invite link when a new user joins."""
    new_members = update.message.new_chat_members
    if new_members:
        for member in new_members:
            send_log(context, f"**[User Joined]** [{member.full_name}](tg://user?id={member.id})")
        generate_invite_link(context)  # Generate a new link when someone joins


def main():
    updater = Updater(API_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("set", set_expiry_time, pass_args=True))

    # Member join handler
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, on_new_member))

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
