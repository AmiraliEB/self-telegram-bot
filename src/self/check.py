import asyncio

from telethon import TelegramClient

from self.config import API_HASH, API_ID

phone = "+989015546102"  # شماره تلفن به همراه کد 98+


async def main():
    client = TelegramClient("test_check", API_ID, API_HASH)
    await client.connect()

    # درخواست مستقیم ارسال کد و دریافت پاسخ سرور
    response = await client.send_code_request(phone)

    # بررسی نوع ارسالی که تلگرام انجام داده
    delivery_type = type(response.type).__name__
    print(f"\n>>> روش ارسال کد توسط تلگرام: {delivery_type} <<<\n")

    await client.disconnect()


asyncio.run(main())
