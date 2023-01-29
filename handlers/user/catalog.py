
import logging
from aiogram.types import Message, CallbackQuery
from keyboards.inline.categories import categories_markup, category_cb
from keyboards.inline.products_from_catalog import product_markup, product_cb, categories_markup_test
from aiogram.utils.callback_data import CallbackData
from aiogram.types.chat import ChatActions
from loader import dp, db, bot, logger
from .menu import catalog
from filters import IsUser
import ast


@dp.message_handler(IsUser(), text=catalog)
async def process_catalog(message: Message):
    await message.answer('Оберіть розділ, щоб вивести список товарів:',
                         reply_markup=categories_markup())


@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):
    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?) 
    AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))
    await bot.answer_callback_query(query.id)
    ls = []
    for idx, title, _, _, _, _, _ in products:
        ls.append((title,idx))
    await query.message.answer('Оберіть товари зі списку 👇 '
                               '\nКільсть кожного товару'
                               '\nможна додати в 🛒Корзині', reply_markup=categories_markup_test(ls))
    # await show_products_test(query.message, products)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='add'))
async def add_product_callback_handler(query: CallbackQuery, callback_data: dict):
    logger.info(f"User id - {query.from_user.id} name - {query.from_user.first_name} add product in cart in cart")
    db.query('INSERT INTO cart VALUES (?, ?, "", 1)',
             (query.message.chat.id, callback_data['id']))

    await query.answer('Товар додано в корзину!')
    await query.message.delete()

async def show_products_test(m, products):
    if len(products) == 0:

        await m.answer('Тут нічого немає 😢')

    else:
        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)
        ls = []
        for idx, title, _, _, _, _, _ in products:
            ls.append((title,idx))

        await m.answer(text="ось всі товари",reply_markup=categories_markup_test(ls))

@dp.callback_query_handler(IsUser(), product_cb.filter(action='view'))
async def show_products_test2(query: CallbackQuery, callback_data: dict):
    await bot.answer_callback_query(query.id)
    products = db.fetchall('''SELECT * FROM products WHERE idx = ?''',(callback_data['id'], ))
    products = products[-1]
    _, title, body, image, price, _, additives = products
    logger.info(f"User id - {query.from_user.id} name - {query.from_user.first_name} looked {title}")
    markup = product_markup(callback_data["id"], price)
    text = f'<b>{title}</b>\n\n{body} '
    #additives = ast.literal_eval(additives)
    #for i in additives:
    #    text += f" • {i}\n"
    #text+="Додати добавку можна в Корзині"

    await query.message.answer_photo(photo=image,
                            caption=text,
                            reply_markup=markup)

@dp.callback_query_handler(IsUser(), product_cb.filter(action='delete'))
async def show_products_test2(query: CallbackQuery, callback_data: dict):
    await query.message.delete()
    # await bot.delete_message(query.message.chat.id, query.message.message_id)

async def show_products(m, products):

    if len(products) == 0:

        await m.answer('Тут нічого немає 😢')

    else:

        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

        for idx, title, body, image, price, _, additives in products:
            markup = product_markup(idx, price)
            text = f'<b>{title}</b>\n\n{body} '
            additives = ast.literal_eval(additives)
            #for i in additives:
            #    text += f" • {i}\n"
            #text+="Додати добавку можна в Корзині"

            await m.answer_photo(photo=image,
                                 caption=text,
                                 reply_markup=markup)
