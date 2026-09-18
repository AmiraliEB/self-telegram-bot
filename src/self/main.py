import asyncio
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


with client:
    print("⚡ Bot is active and listening for challenges...")
    client.run_until_disconnected()
