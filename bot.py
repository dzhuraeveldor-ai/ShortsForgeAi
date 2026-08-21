import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiohttp import web

BOT_TOKEN = "8984766153:AAGKVpwZkPeMYmByrY69o-gBFO3ZE6vaJzE"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("✅ БОТ РАБОТАЕТ! УРА!")

async def bot_startup(app):
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot))

async def health_check(request):
    return web.Response(text="OK")

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    app.on_startup.append(bot_startup)
    web.run_app(app, port=PORT)
