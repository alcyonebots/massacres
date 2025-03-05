import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

# API credentials
api_id = 22878444
api_hash = "550641aa3600a98c1cb94afc259f2244"
bot_token = "8151182853:AAGweMO0CZkaFMZxzYRVoxoC5pbAJHtlXBs"

app = Client("massacres", api_id, api_hash, bot_token=bot_token)

# Configuration
GROUP_ID = -1002033219914  # Private group ID
CHANNEL_ID = -1001761041493  # Channel ID
MESSAGE_ID = 9  # Fixed message ID in the channel
OWNER_ID = 6663845789  # Owner's Telegram ID for logs

current_invite_link = None

def send_log(text):
    """Send logs to the owner's DM."""
    try:
        app.send_message(OWNER_ID, f"📜 *Log Update:*\n{text}", parse_mode="markdown")
    except Exception as e:
        print(f"Error sending log: {e}")

def revoke_existing_links():
    """Revoke all active invite links in the group."""
    try:
        links = app.get_chat_invite_links(GROUP_ID)
        for link in links:
            if not link.is_revoked:
                app.revoke_chat_invite_link(GROUP_ID, link.invite_link)
                send_log(f"Revoked invite link: {link.invite_link}")
    except Exception as e:
        send_log(f"Error revoking links: {e}")

def create_invite_link():
    """Generate a new invite link."""
    global current_invite_link
    try:
        invite = app.create_chat_invite_link(GROUP_ID, expire_date=datetime.utcnow() + timedelta(minutes=1))
        current_invite_link = invite.invite_link
        send_log(f"New invite link created: {current_invite_link}")
    except Exception as e:
        send_log(f"Error creating invite link: {e}")
        return None
    return current_invite_link

def update_invite_link():
    """Loop to update invite links and edit the message button."""
    global current_invite_link
    while True:
        revoke_existing_links()
        new_link = create_invite_link()
        if new_link:
            try:
                new_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Group", url=new_link)]])
                app.edit_message_reply_markup(CHANNEL_ID, MESSAGE_ID, reply_markup=new_markup)
                send_log("Updated inline button in the fixed message.")
            except Exception as e:
                send_log(f"Error updating inline button: {e}")

        time.sleep(60)  # Wait 1 minute before regenerating

@app.on_message(filters.new_chat_members)
def on_new_member(_, message):
    """Revoke invite link once a new member joins."""
    global current_invite_link
    if current_invite_link:
        try:
            app.revoke_chat_invite_link(GROUP_ID, current_invite_link)
            send_log(f"Invite link revoked after {message.from_user.mention} joined.")
        except Exception as e:
            send_log(f"Error revoking link after user joined: {e}")

if __name__ == "__main__":
    app.start()
    update_invite_link()  # Run the invite link update loop
    app.idle()
