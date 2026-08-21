import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from config import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("✅ Бот работает! Привет!")

async def main():
    await dp.start_polling(bot)

os.environ.setdefault("PORT", "10000")

if __name__ == "__main__":
    asyncio.run(main())
