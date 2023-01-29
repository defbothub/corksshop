
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ContentType, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from states import ProductState, CategoryState
from aiogram.types.chat import ChatActions
from handlers.user.menu import settings
from loader import dp, db, bot, logger
from filters import IsAdmin
from hashlib import md5
import ast


category_cb = CallbackData('category', 'id', 'action')
product_cb = CallbackData('product', 'id', 'action')

add_product = '➕ Додати товар'
delete_category = '🗑️ Видалити категорію'


@dp.message_handler(IsAdmin(), text=settings)
async def process_settings(message: Message):

    markup = InlineKeyboardMarkup()

    for idx, title in db.fetchall('SELECT * FROM categories'):

        markup.add(InlineKeyboardButton(
            title, callback_data=category_cb.new(id=idx, action='view')))

    markup.add(InlineKeyboardButton(
        '+ Додати категорію', callback_data='add_category'))

    await message.answer('Налаштування категорій:', reply_markup=markup)


@dp.callback_query_handler(IsAdmin(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):

    category_idx = callback_data['id']

    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?)''',
                           (category_idx,))

    await query.message.delete()
    await query.answer('Всі додані товари в цю категорію.')
    await state.update_data(category_index=category_idx)
    await show_products(query.message, products)


# category


@dp.callback_query_handler(IsAdmin(), text='add_category')
async def add_category_callback_handler(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('Яка назва категорії?', reply_markup=menu_markup())
    await CategoryState.title.set()


@dp.message_handler(IsAdmin(), state=CategoryState.title)
async def set_category_title_handler(message: Message, state: FSMContext):

    category = message.text
    logger.info(f"Admin id - {message.from_user.id} name - {message.from_user.first_name} add category {category}")
    idx = md5(category.encode('utf-8')).hexdigest()
    db.query('INSERT INTO categories VALUES (?, ?)', (idx, category))
    await state.finish()
    await process_settings(message)


@dp.message_handler(IsAdmin(), text=delete_category)
async def delete_category_handler(message: Message, state: FSMContext):

    async with state.proxy() as data:
        if 'category_index' in data.keys():
            logger.info(f"Admin id - {message.from_user.id} name - {message.from_user.first_name} add category {message.text}")
            idx = data['category_index']
            db.query(
                'DELETE FROM products WHERE tag IN (SELECT title FROM categories WHERE idx=?)', (idx,))
            db.query('DELETE FROM categories WHERE idx=?', (idx,))

            await message.answer('Готово!', reply_markup=menu_markup())
            await process_settings(message)


# add product


@dp.message_handler(IsAdmin(), text=add_product)
async def process_add_product(message: Message):

    await ProductState.title.set()

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(cancel_message)

    await message.answer('Яка назва?', reply_markup=markup)


@dp.message_handler(IsAdmin(), text=cancel_message, state=ProductState.title)
async def process_cancel(message: Message, state: FSMContext):

    await message.answer('Ок, відмінено!', reply_markup=menu_markup())
    await state.finish()

    await process_settings(message)


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.title)
async def process_title_back(message: Message, state: FSMContext):
    await process_add_product(message)


@dp.message_handler(IsAdmin(), state=ProductState.title)
async def process_title(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['title'] = message.text
        data['additives'] = {}
        data['additive_queue'] = []

    await ProductState.next()
    await message.answer('Який опис?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.body)
async def process_body_back(message: Message, state: FSMContext):

    await ProductState.title.set()

    async with state.proxy() as data:

        await message.answer(f"Змінити назву з <b>{data['title']}</b>?", reply_markup=back_markup())


@dp.message_handler(IsAdmin(), state=ProductState.body)
async def process_body(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['body'] = message.text

    await ProductState.next()
    await message.answer('Яке фото?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), content_types=ContentType.PHOTO, state=ProductState.image)
async def process_image_photo(message: Message, state: FSMContext):

    fileID = message.photo[-1].file_id
    file_info = await bot.get_file(fileID)
    downloaded_file = (await bot.download_file(file_info.file_path)).read()

    async with state.proxy() as data:
        data['image'] = downloaded_file

    await ProductState.next()
    await message.answer('Яка ціна?', reply_markup=back_markup())


@dp.message_handler(IsAdmin(), content_types=ContentType.TEXT, state=ProductState.image)
async def process_image_url(message: Message, state: FSMContext):

    if message.text == back_message:

        await ProductState.body.set()

        async with state.proxy() as data:

            await message.answer(f"Змінити опис з <b>{data['body']}</b>?", reply_markup=back_markup())

    else:

        await message.answer('Потрібно прислати фото товару.')


@dp.message_handler(IsAdmin(), lambda message: not message.text.isdigit(), state=ProductState.price)
async def process_price_invalid(message: Message, state: FSMContext):

    if message.text == back_message:

        await ProductState.image.set()

        async with state.proxy() as data:

            await message.answer("Замінити зображення на інше?", reply_markup=back_markup())

    else:

        await message.answer('Вкажіть ціну у вигляді числа!')


@dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(), state=ProductState.price)
async def process_price(message: Message, state: FSMContext):
    async with state.proxy() as data:

        title = data['title']
        body = data['body']
        data['price'] = message.text
        price = data['price']

        await ProductState.confirm.set()
        text = f'<b>{title}</b>\n\n{body}\n\nЦіна за 1 шт. - {price}'

        markup = check_markup()

        await message.answer_photo(photo=data['image'],
                                caption=text,
                                reply_markup=markup)

# @dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(), state=ProductState.price)
# async def process_price(message: Message, state: FSMContext):
#
#     async with state.proxy() as data:
#
#         data['price'] = message.text
#
#         await ProductState.next()
#         await message.answer(f"Додати добавку? {data['additives']}", reply_markup=back_markup())
#
# @dp.message_handler(IsAdmin(), content_types=ContentType.TEXT, state=ProductState.additive)
# async def process_price(message: Message, state: FSMContext):
#     if message.text == back_message:
#         async with state.proxy() as data:
#             if len(data["additive_queue"]) == 0:
#                 data["additive_queue"] = []
#                 data['additives'] = {}
#                 await ProductState.price.set()
#                 await message.answer(f"Змінити ціну з <b>{data['price']}</b>?", reply_markup=back_markup())
#             else:
#                 now_additive = data["additive_queue"][-1]
#                 await ProductState.additive_price.set()
#                 await message.answer(f"{now_additive} Змінити ціну з <b>{data['additives'][now_additive]}</b>?", reply_markup=back_markup())
#     elif message.text == end_add_adivives_message:
#         async with state.proxy() as data:
#
#             title = data['title']
#             body = data['body']
#             price = data['price']
#             additives = data['additives']
#
#             await ProductState.confirm.set()
#             text = f'<b>{title}</b>\n\n{body}\nДобавки:\n'
#             for i in additives.keys():
#                 text += f"• {i} - {additives[i]}\n"
#
#             text+=f"Ціна за 1 шт. - {price} "
#
#             markup = check_markup()
#
#             await message.answer_photo(photo=data['image'],
#                                     caption=text,
#                                     reply_markup=markup)
#
#     else:
#         async with state.proxy() as data:
#
#             additives_dict = data['additives']
#             additives_dict[message.text] = 0
#             data['additives'] = additives_dict
#             data['additive_queue'].append(message.text)
#
#             await ProductState.next()
#             await message.answer(f"Ціна добавки <b>{message.text}</b>?", reply_markup=back_markup())
#
# @dp.message_handler(IsAdmin(), lambda message: not message.text.isdigit(), state=ProductState.additive_price)
# async def process_price_invalid(message: Message, state: FSMContext):
#     if message.text == back_message:
#         async with state.proxy() as data:
#             if data['additive_queue'] == []:
#                 await ProductState.price.set()
#                 await message.answer(f"Змінити ціну з <b>{data['price']}</b>?", reply_markup=back_markup())
#             else:
#                 now_additive = data['additive_queue'].pop()
#                 await ProductState.additive.set()
#                 del data['additives'][now_additive]
#                 await message.answer(f"Змінити назву <b>{now_additive}</b>? {data['additives']}", reply_markup=back_markup())
#
#     else:
#
#         await message.answer('Вкажіть ціну у вигляді числа!')
#
# @dp.message_handler(IsAdmin(), lambda message: message.text.isdigit(), state=ProductState.additive_price)
# async def process_price(message: Message, state: FSMContext):
#
#     async with state.proxy() as data:
#         #= message.text
#         now_additive = data['additive_queue'][-1]
#         additives_dict = data['additives']
#         additives_dict[now_additive] = int(message.text)
#         data['additives'] = additives_dict
#
#         await ProductState.additive.set()
#
#         await message.answer(f"Додати добавку? {data['additives']}", reply_markup=back_addetive_markup())


@dp.message_handler(IsAdmin(), lambda message: message.text not in [back_message, all_right_message], state=ProductState.confirm)
async def process_confirm_invalid(message: Message, state: FSMContext):
    await message.answer('Такого варіанту не було.')


@dp.message_handler(IsAdmin(), text=back_message, state=ProductState.confirm)
async def process_confirm_back(message: Message, state: FSMContext):

    await ProductState.price.set()

    async with state.proxy() as data:
        now_additive = data["additive_queue"][-1]
        await ProductState.additive_price.set()
        await message.answer(f"{now_additive} Змінити ціну з <b>{data['additives'][now_additive]}</b>?", reply_markup=back_markup())


@dp.message_handler(IsAdmin(), text=all_right_message, state=ProductState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    async with state.proxy() as data:

        title = data['title']
        body = data['body']
        image = data['image']
        price = data['price']
        additives = data['additives']

        tag = db.fetchone(
            'SELECT title FROM categories WHERE idx=?', (data['category_index'],))[0]
        idx = md5(' '.join([title, body, price, tag]
                           ).encode('utf-8')).hexdigest()
        logger.info(f"Admin id - {message.from_user.id} name - {message.from_user.first_name} add product {title} into {data['category_index']}")
        db.query('INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (idx, title, body, image, int(price), tag, str(additives)))

    await state.finish()
    await message.answer('Готово!', reply_markup=ReplyKeyboardRemove())
    await process_settings(message)


# delete product


@dp.callback_query_handler(IsAdmin(), product_cb.filter(action='delete'))
async def delete_product_callback_handler(query: CallbackQuery, callback_data: dict):

    product_idx = callback_data['id']
    logger.info(f"Admin id - {query.from_user.id} name - {query.from_user.first_name} delete product with index - {product_idx}")
    db.query('DELETE FROM products WHERE idx=?', (product_idx,))
    await query.answer('Видалено!')
    await query.message.delete()


async def show_products(m, products):

    await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

    for idx, title, body, image, price, tag, aditives in products:
        aditives = ast.literal_eval(aditives)
        text = f'<b>{title}</b>\n\n{body}\n\n'
        for i in aditives.keys():
            text += f"• {i} - {aditives[i]}\n"
            
        text+=f"\nЦіна за 1 шт. - {price} ₴"

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            '🗑️ Видалити', callback_data=product_cb.new(id=idx, action='delete')))

        await m.answer_photo(photo=image,
                             caption=text,
                             reply_markup=markup)

    markup = ReplyKeyboardMarkup()
    markup.add(add_product)
    markup.add(delete_category)
    markup.add(menu_message)

    await m.answer('Хочете щось додати чи видалити?', reply_markup=markup)
