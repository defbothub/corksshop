from data.config import sale_photo, adress
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from loader import dp
from keyboards import *
from filters import IsAdmin, IsUser

catalog = '🍾 Винна карта'
cart = '🛒 Корзина'
sale = '🎁  Акція'
contacts = '☎ Контакти'

settings = '⚙ Налаштування винної карти'
orders = '🚚 Замовлення'

@dp.message_handler(IsAdmin(), text=menu_message)
async def admin_menu(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(settings)
    markup.add(orders)
    await message.answer('Меню', reply_markup=markup)

@dp.message_handler(IsUser(), text=menu_message)
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(catalog)
    markup.insert(cart)
    markup.add(sale).insert(contacts)
    await message.answer('Меню', reply_markup=markup)

@dp.message_handler(IsUser(), text=sale)
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(catalog)
    markup.insert(cart)
    markup.add(sale).insert(contacts)
    await message.answer_photo(sale_photo, reply_markup=markup)
    await message.answer('Збери 50 корків і отримай знижку 5% на пляшку вина.')

@dp.message_handler(IsUser(), text=contacts)
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(catalog)
    markup.insert(cart)
    markup.add(sale).insert(contacts)
    await message.answer_photo(adress, reply_markup=markup)
    await message.answer('Катерина')
    await message.answer('+380977757652')
    await message.answer("🔹Доставка по місту Бровари 100 грн.\n🔹При замовленні від 4-х пляшок доставка безкоштовна.\n🔹Щоп’ятниці безкоштовна доставка по місту.\n🔹По Україні доставляємо Новою поштою.\nБезкоштовна доставка Новою Поштою при замовленні від 4-х пляшок в поштомат.")


