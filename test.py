import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

# API credentials
api_id = 22878444
api_hash = "550641aa3600a98c1cb94afc259f2244"
bot_token = "8151182853:AAGweMO0CZkaFMZxzYRVoxoC5pbAJHtlXBs"

app = Client("massacres", api_id, api_hash, bot_token=bot_token)

# Configuration
GROUP_ID = -1002033219914  
CHANNEL_ID = -1001761041493  
MESSAGE_ID = 9  
OWNER_ID = 6663845789  

current_invite_link = None

async def send_log(text):
    """Send logs to the owner's DM."""
    try:
        await app.send_message(OWNER_ID, f"📜 {text}")
    except Exception as e:
        print(f"Error sending log: {e}")

async def revoke_existing_links():
    """Revoke all active invite links in the group."""
    try:
        links = await app.get_chat_invite_links(GROUP_ID)
        for link in links:
            if not link.is_revoked:
                await app.revoke_chat_invite_link(GROUP_ID, link.invite_link)
                await send_log(f"Revoked invite link: {link.invite_link}")
    except Exception as e:
        await send_log(f"Error revoking links: {e}")

async def create_invite_link():
    """Generate a new invite link."""
    global current_invite_link
    try:
        invite = await app.create_chat_invite_link(GROUP_ID, expire_date=datetime.utcnow() + timedelta(minutes=1))
        current_invite_link = invite.invite_link
        await send_log(f"New invite link created: {current_invite_link}")
    except Exception as e:
        await send_log(f"Error creating invite link: {e}")
        return None
    return current_invite_link

async def update_invite_link():
    """Loop to update invite links and edit only the button."""
    global current_invite_link
    while True:
        await revoke_existing_links()
        new_link = await create_invite_link()
        if new_link:
            try:
                new_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Group", url=new_link)]])
                
                # ✅ Only Update Inline Button
                await app.edit_message_reply_markup(CHANNEL_ID, MESSAGE_ID, reply_markup=new_markup)
                await send_log("✅ Inline button updated successfully.")
            except Exception as e:
                await send_log(f"⚠️ Error updating button: {e}")

        await asyncio.sleep(60)  # Wait 1 minute before regenerating

@app.on_message(filters.new_chat_members)
async def on_new_member(_, message):
    """Revoke invite link once a new member joins."""
    global current_invite_link
    if current_invite_link:
        try:
            await app.revoke_chat_invite_link(GROUP_ID, current_invite_link)
            await send_log(f"Invite link revoked after {message.from_user.mention} joined.")
        except Exception as e:
            await send_log(f"Error revoking link after user joined: {e}")

async def main():
    await app.start()
    asyncio.create_task(update_invite_link())
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())  # Async entry point
