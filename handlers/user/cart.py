import logging
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline.products_from_cart import product_markup, product_cb, additeve_cb
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from aiogram.types.chat import ChatActions
from states import CheckoutState
from loader import dp, db, bot, logger
from filters import IsUser
from .menu import cart
import re
import ast
import json

def myAtoi(str):
    str = str.strip()
    str = re.findall('(^[\+\-0]*\d+)\D*', str)
    try:
        result = int(''.join(str))
        return max(-2**31, min(result,2**31-1))
    except:
        return 0

@dp.message_handler(IsUser(), text=cart)
async def process_cart(message: Message, state: FSMContext):
    logger.info(f"User id - {message.from_user.id} name - {message.from_user.first_name} showed all products in cart")
    cart_data = db.fetchall(
        'SELECT * FROM cart WHERE cid=?', (message.chat.id,))

    if len(cart_data) == 0:

        await message.answer('Ваша корзина порожня.')

    else:

        await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
        async with state.proxy() as data:
            data['products'] = {}


        order_cost = 0

        for _, idx, _, count_in_cart in cart_data:

            product = db.fetchone('SELECT * FROM products WHERE idx=?', (idx,))

            if product == None:

                db.query('DELETE FROM cart WHERE idx=?', (idx,))

            else:
                _, title, body, image, price, _, additives = product
                order_cost += price

                async with state.proxy() as data:
                    data['products'][idx] = [title, price, count_in_cart, additives, []]
                markup = product_markup(idx, count_in_cart, additives)
                text = f'{title}\n\n{body}\n\nЦіна за 1 шт. -  {price} ₴.'

                await message.answer_photo(photo=image,
                                           caption=text,
                                           reply_markup=markup)

        if order_cost != 0:

            await message.answer('Перейти до оформлення?',
                                 reply_markup=cart_markup())

# @dp.callback_query_handler(IsUser(), additeve_cb.filter(isactive="0"))
# @dp.callback_query_handler(IsUser(), additeve_cb.filter(isactive="1"))
# async def additeve_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):
#     title = callback_data['title']
#     logger.info(f"User id - {query.from_user.id} name - {query.from_user.first_name} changed state {title}")
#     isactive = callback_data['isactive']
#     idx = callback_data['id']
#     caption = dict(query)['message']['caption']
#     l = int(caption.find('Ціна за 1: '))+len('Ціна за 1: ')
#     body_text = caption[:l]
#     total_price = myAtoi(caption[l:-1])
#     async with state.proxy() as data:
#         count_in_cart = data['products'][idx][2]
#         additives = data['products'][idx][3]
#         temp_additives = (additives + '.')[:-1]
#         temp_additives = ast.literal_eval(temp_additives)
#         if isactive == "1":
#             if title in data['products'][idx][4]:
#                 data['products'][idx][4].remove(title)
#                 total_price -= temp_additives[title]
#                 db.query('''UPDATE cart
#                     SET iddarr = ?
#                     WHERE cid = ? AND idx = ?''', (json.dumps(data['products'][idx][4]), query.message.chat.id, idx))
#         else:
#             data['products'][idx][4].append(title)
#             total_price += temp_additives[title]
#             db.query('''UPDATE cart
#                     SET iddarr = ?
#                     WHERE cid = ? AND idx = ?''', (json.dumps(data['products'][idx][4],ensure_ascii=True), query.message.chat.id, idx))
#         caption = body_text + str(total_price) + "грн."
#         await query.message.edit_caption(caption,reply_markup=product_markup(idx, count_in_cart, additives, data['products'][idx][4]))


@dp.callback_query_handler(IsUser(), product_cb.filter(action='count'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='increase'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='decrease'))
async def product_callback_handler(query: CallbackQuery, callback_data: dict, state: FSMContext):

    idx = callback_data['id']
    action = callback_data['action']

    if 'count' == action:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                await query.answer('Кількість - ' + str(data['products'][idx][2]))

    else:

        async with state.proxy() as data:

            if 'products' not in data.keys():

                await process_cart(query.message, state)

            else:

                data['products'][idx][2] += 1 if 'increase' == action else -1
                count_in_cart = data['products'][idx][2]
                additives = data['products'][idx][3]
                active_additives = data['products'][idx][4]

                if count_in_cart == 0:

                    db.query('''DELETE FROM cart
                    WHERE cid = ? AND idx = ?''', (query.message.chat.id, idx))

                    await query.message.delete()
                else:
                    db.query('''UPDATE cart 
                    SET quantity = ? 
                    WHERE cid = ? AND idx = ?''', (count_in_cart, query.message.chat.id, idx))

                    await query.message.edit_reply_markup(product_markup(idx, count_in_cart, additives, active_additives))


@dp.message_handler(IsUser(), text=checkout_message)
async def process_checkout(message: Message, state: FSMContext):

    await CheckoutState.check_cart.set()
    await checkout(message, state)


#async def checkout(message, state):
#    answer = ''
#    total_price = 0

    # async with state.proxy() as data:
    #
    #     for title, price, count_in_cart, additionals, active_additionals in data['products'].values():
    #         temp_additives = ast.literal_eval(additionals)
    #         tp = price
    #         answer += f"<b>{title}</b> {count_in_cart}шт. {price} ₴\nДодаткові добавки:\n"
    #         for i in active_additionals:
    #             answer += " • \""+i+f"\" по ціні - {temp_additives[i]} ₴\n"
    #             tp += temp_additives[i]
    #         answer += f'<b>{tp * count_in_cart} ₴</b>\n'
    #
    #         total_price += tp * count_in_cart
    #
    # await message.answer(f'{answer}\nЗагальна сума замовлення: {total_price} ₴.',
    #                      reply_markup=check_markup())


async def checkout(message, state):
    answer = ''
    total_price = 0

    async with state.proxy() as data:
        for title, price, count_in_cart, _, active_additionals in data['products'].values():
            tp = price
            answer += f"<b>{title}</b> {count_in_cart} шт. по {price} ₴\n"
            answer += f'<b>Разом - {tp * count_in_cart} ₴</b>\n'

            total_price += tp * count_in_cart

    await message.answer(f'{answer}\nЗагальна сума замовлення: {total_price} ₴',
                         reply_markup=check_markup())


@dp.message_handler(IsUser(), text=cancel_cart_message)
async def clear_cart(message: Message, state: FSMContext):
    logger.info(f"User id - {message.from_user.id} name - {message.from_user.first_name} clear a cart.")
    db.query('''DELETE FROM cart WHERE cid = ?''', (message.chat.id,))
    await message.answer("Корзина очищена.\nТисніть Menu, щоб продовжити.", reply_markup=menu_markup())


@dp.message_handler(IsUser(), lambda message: message.text not in [all_right_message, back_message], state=CheckoutState.check_cart)
async def process_check_cart_invalid(message: Message):
    await message.reply('Такого варіанту не було.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    await state.finish()
    await process_cart(message, state)


@dp.message_handler(IsUser(), text=all_right_message, state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):
    await CheckoutState.next()
    await message.answer("Вкажіть свій номер телефону.",
                         reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):
    await CheckoutState.check_cart.set()
    await checkout(message, state)


@dp.message_handler(IsUser(), state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):

    async with state.proxy() as data:

        data['name'] = message.text

        if 'address' in data.keys():

            await confirm(message)
            await CheckoutState.confirm.set()

        else:

            await CheckoutState.next()
            await message.answer("🔹Доставка по місту Бровари 100 грн."
                                 "\nПри замовленні від 4-х пляшок доставка безкоштовна. "
                                 "Щоп’ятниці безкоштовна доставка по місту, якщо бажаєте, "
                                 "додайте в кінці адреси слово (п'ятниця). "
                                 "\n🔹По Україні доставляємо Новою поштою."
                                 "\nБезкоштовна доставка Новою Поштою при замовленні від 4-х пляшок в поштомат."
                                 "\n🔹Вкажіть адресу доставки.",
                                 reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):

    async with state.proxy() as data:

        await message.answer("Змінити номер з <b>" + data['name'] + '</b>?',
                             reply_markup=back_markup())

    await CheckoutState.name.set()


@dp.message_handler(IsUser(), state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):

    async with state.proxy() as data:
        data['address'] = message.text

    await confirm(message)
    await CheckoutState.next()


async def confirm(message):

    await message.answer('Перевірте чи все правильно оформлено і підтвердіть замовлення.',
                         reply_markup=confirm_markup())


@dp.message_handler(IsUser(), lambda message: message.text not in [confirm_message, back_message], state=CheckoutState.confirm)
async def process_confirm_invalid(message: Message):
    await message.reply('Такого варіанту не було.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):

    await CheckoutState.address.set()

    async with state.proxy() as data:
        await message.answer('Змінити адресу з <b>' + data['address'] + '</b>?',
                             reply_markup=back_markup())


@dp.message_handler(IsUser(), text=confirm_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    markup = ReplyKeyboardRemove()
    logger.info(f"User id - {message.from_user.id} name - {message.from_user.first_name} Deal was made.")

    async with state.proxy() as data:

        cid = message.chat.id
        products = {}
        for idx, quantity, active_additives in db.fetchall('''SELECT idx, quantity, iddarr FROM cart WHERE cid=?''', (cid,)):
            active_additives = json.loads(active_additives) if active_additives!="" else {}
            products[idx] = {"quantity":quantity, 'active_additives':active_additives}

        db.query('INSERT INTO orders VALUES (?, ?, ?, ?, ?)',
                    (None, cid, data['name'], data['address'], json.dumps(products, ensure_ascii=True)))

        db.query('DELETE FROM cart WHERE cid=?', (cid,))

        await message.answer("Ок! Ваше замовлення прийняте. \nТелефон: <b>" + data['name'] + '</b>\nАдреса: <b>' + data['address'] + '</b>',
                                reply_markup=markup)


    await state.finish()
    await bot.send_message(chat_id=5791823682, text="Нове замовлення!")
    await message.answer("Дякуємо за замовлення! \nЩоб продовжити покупки, натисніть Menu", reply_markup=menu_markup())