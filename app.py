
import os
import handlers
from keyboards import *
from aiogram import executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from data import config
from loader import dp, db, bot
import filters
import logging
import aioschedule
import asyncio
import datetime

filters.setup(dp)

#user_message = 'Користувач'
#admin_message = 'Адміністратор'


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    #markup = ReplyKeyboardMarkup(resize_keyboard=True)
    #markup.row(user_message, admin_message)
    cid = message.chat.id
    if cid in config.ADMINS:
        config.ADMINS.append(cid)
        await message.answer('Вітаю тебе моя господине, Катерино!'
                             '\nГарного робочого дня 🤗'
                             '\nТисни Menu і почнемо...', reply_markup=menu_markup())
    else:
        await message.answer('''Бот винного бутіка CORKS вітає Вас! Натисніть Menu, щоб продовжити.   👇''',
                             reply_markup=menu_markup())

# @dp.message_handler(text=user_message)
# async def user_mode(message: types.Message):
#     cid = message.chat.id
#     if cid not in config.ADMINS:
#         config.ADMINS.remove(cid)
#     await message.answer('Увімкнено режим користувача.', reply_markup=menu_markup())
#
# @dp.message_handler(text=admin_message)
# async def admin_mode(message: types.Message):
#     cid = message.chat.id
#     if cid in config.ADMINS:
#         config.ADMINS.append(cid)
#     await message.answer('Увімкнено режим адміністратора.', reply_markup=menu_markup())

def something():
    day_of_month = datetime.now().day
    if (day_of_month > 7 and day_of_month < 15) or day_of_month > 21:
        db.query("DELETE FROM orders;")

async def scheduler():
    aioschedule.every().monday.at("23:19").do(something)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(dp):
    logging.basicConfig(level=logging.INFO)
    db.create_tables()


async def on_shutdown():
    logging.warning("Shutting down..")
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bot down")

executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
