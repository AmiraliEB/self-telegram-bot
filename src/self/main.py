import asyncio
import io
import logging
import re
import time

import aiohttp
from telethon import TelegramClient, events

from self.config import ADMIN_ID, API_HASH, API_ID, DISCUSSION_GROUP_ID, NTFY_TOPIC_ID

logging.basicConfig(
    format="[%(levelname)s %(asctime)s] %(name)s: %(message)s",
    level=logging.WARNING,
)

client = TelegramClient("amir", API_ID, API_HASH)

CHALLENGE_PATTERN = re.compile(
    r"(?s)این\s*(?:پایین|زیر).*?بگه\s*[:：]?\s*[\r\n]*\s*[*_`~\"'«]?(?P<target>[^\r\n*_`~\"'»]+?)[*_`~\"'»]?(?:\s+|[\r\n]+[^\w\s]*\s*)برنده.*?میشه"
)


async def send_urgent_alarm(message: str) -> None:
    url = "https://ntfy.sh"
    payload = {
        "topic": NTFY_TOPIC_ID,
        "title": "🚨 Challenge Won!",
        "message": message,
        "priority": 5,  # Maximum priority for instant sound & vibration
        "tags": ["tada", "warning"],
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=5) as response:
                if response.status == 200:
                    print("🔔 Notification sent successfully to device.")
                else:
                    print(f"⚠️ ntfy returned status code: {response.status}")
    except Exception as e:
        print(f"⚠️ Network error while dispatching notification: {e}")


@client.on(events.NewMessage(chats=DISCUSSION_GROUP_ID))
async def challenge_listener(event: events.NewMessage.Event):
    if not (event.fwd_from and event.fwd_from.from_id):
        return

    start_time = time.perf_counter()
    match = CHALLENGE_PATTERN.search(event.raw_text)
    t_regex = time.perf_counter()

    if match:
        target_phrase = match.group("target").strip(" *`\t\r\n")

        if 2 <= len(target_phrase) <= 15:
            print(f"🎯 Target phrase found: [{target_phrase}]")

            try:
                await event.reply(target_phrase)
                t_sent = time.perf_counter()

                regex_ms = (t_regex - start_time) * 1000
                network_ms = (t_sent - t_regex) * 1000
                total_ms = (t_sent - start_time) * 1000

                print(f"✅ Comment posted successfully: {target_phrase}")
                print(f"⏱ Regex parsing: {regex_ms:.3f} ms")
                print(f"⏱ Network request: {network_ms:.2f} ms")
                print(f"⏱ Total latency: {total_ms:.2f} ms")
                channel_entity = await client.get_entity(event.fwd_from.from_id)
                channel_username = channel_entity.username
                if channel_username:
                    post_link = f"https://t.me/{channel_username}/{event.fwd_from.channel_post}"
                else:
                    post_link = f"https://t.me/c/{event.fwd_from.from_id.channel_id}/{event.fwd_from.channel_post}"
                await client.send_message(ADMIN_ID, f"برنده چالش کانال زیر شدی \n{post_link}")
                print(f"✅ message send to admin successfully: {ADMIN_ID}")
                # Dispatch notification in the background to avoid blocking execution
                asyncio.create_task(send_urgent_alarm(f"Comment posted: {target_phrase}"))

            except Exception as e:
                print(f"❌ Error sending comment: {e}")


@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\s*ping\s*$"))
async def ping_edit_listener(event: events.NewMessage.Event):
    try:
        start_time = time.perf_counter()

        await event.edit("🏓 Pong!")
        latency_ms = (time.perf_counter() - start_time) * 1000
        await event.edit(f"🏓 **Pong!**\n⏱ Ping: `{latency_ms:.1f}` ms")
        await asyncio.sleep(5)

        await event.delete()

    except Exception as e:
        print(f"❌ error in ping pong method: {e}")


def extract_ttl(msg):
    media = getattr(msg, "media", None)
    if not media:
        return None

    ttl = getattr(media, "ttl_seconds", None)
    if not ttl and getattr(media, "document", None):
        for attr in getattr(media.document, "attributes", []):
            attr_ttl = getattr(attr, "ttl_seconds", None)
            if attr_ttl:
                return attr_ttl
    return ttl


@client.on(events.NewMessage(incoming=True, func=lambda event: event.is_private and (event.photo or event.video)))
async def private_message_handler(event: events.NewMessage.Event):
    msg = event.message
    ttl = extract_ttl(msg)

    if not ttl or ttl <= 0:
        return

    if ttl >= 2147483647 or ttl == 1:
        media_label = "View Once"
    else:
        media_label = f"Timer ({ttl}s)"

    if msg.voice:
        filename = "voice.ogg"
    elif msg.video or msg.video_note:
        filename = "video.mp4"
    else:
        filename = "photo.jpg"

    buffer = io.BytesIO()
    await msg.download_media(file=buffer)
    buffer.seek(0)
    buffer.name = filename

    caption = f"save media {media_label}\n" f"sender: {msg.sender_id}"

    await client.send_file("me", buffer, caption=caption, silent=True)


with client:
    print("⚡ Bot is active and listening for challenges...")
    client.run_until_disconnected()
