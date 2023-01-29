
from aiogram.types import Message
from loader import dp, db, logger
from handlers.user.menu import orders
from filters import IsAdmin
import json

@dp.message_handler(IsAdmin(), text=orders)
async def process_orders(message: Message):
    logger.info(f"Admin id - {message.from_user.id} name - {message.from_user.first_name} view orders")
    orders = db.fetchall('SELECT * FROM orders')
    
    if len(orders) == 0: await message.answer('У вас немає замовлень.')
    else: await order_answer(message, orders)


async def order_answer(message, orders):

    res = ''
    st = 0
    for order in orders:
        st+=1
        data = json.loads(order[4])
        res += f"<b>Замовлення</b> N{order[0]} \n<b>Від:</b> {order[2]}\n<b>На адресу:</b> {order[3]}\n"
        for idx in list(data.keys()):
            try:
                name = db.fetchall(f'SELECT title FROM products WHERE idx="{idx}"')[0][0]
            except:
                name = "Товару немає в базі"
            num = data[idx]['quantity']
            active_additives = data[idx]['active_additives']
            res += f'{name}, в кількості-{num} шт.'
            #if active_additives:
            #    for i in active_additives:
            #        res += f"   • {i}\n"
            #else:
            #    res+="немає\n"
        res+="\n\n"

    await message.answer(res)