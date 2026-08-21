import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "8984766153:AAGl5sHCbXT22DQoOvOP7vgPabp5j7fGzKI"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("✅ БОТ РАБОТАЕТ! УРА!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
