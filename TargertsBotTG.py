from aiogram import Bot, Dispatcher
from token import TOKEN
from app.handlers import router
from app.requests import DBC

import asyncio

bot = Bot(token=TOKEN)

dp = Dispatcher()

db = DBC()


async def main():
    dp.include_router(router)
    await db.initialize_pool()
    await dp.start_polling(bot)
    await db.on_shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
