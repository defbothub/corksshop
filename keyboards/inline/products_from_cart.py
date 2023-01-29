from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
import ast

product_cb = CallbackData('product', 'id', 'action')
additeve_cb = CallbackData('additeve', 'id', 'title', 'isactive')

def product_markup(idx, count, additevs:str = "", active_additevs=[]):

    global product_cb
    global additeve_cb

    markup = InlineKeyboardMarkup()
#    additives = ast.literal_eval(additevs)
    additevs_items = [] #list(map(list,additives.items()))
    for i in range(0, len(additevs_items)-1, 2):
        first_name, first_price = additevs_items[i]
        second_name, second_price = additevs_items[i+1]
        # print("active_additevs -",active_additevs)
        if first_name in active_additevs:
            first = InlineKeyboardButton(f"✅ {first_name} - {first_price} грн.", callback_data=additeve_cb.new(id=idx, title=first_name, isactive=1))
        else: 
            first = InlineKeyboardButton(f"❌ {first_name} - {first_price} грн.", callback_data=additeve_cb.new(id=idx, title=first_name, isactive=0))
        
        if second_name in active_additevs:
            second = InlineKeyboardButton(f"✅ {second_name} - {second_price} грн.", callback_data=additeve_cb.new(id=idx, title=second_name, isactive=1))
        else:
            second = InlineKeyboardButton(f"❌ {second_name} - {second_price} грн.", callback_data=additeve_cb.new(id=idx, title=second_name, isactive=0))
        markup.row(first, second)
    if(len(additevs_items)%2==1):
        first_name, first_price = additevs_items[-1]
        if first_name in active_additevs:
            markup.row(InlineKeyboardButton(f"✅ {first_name} - {first_price} грн.", callback_data=additeve_cb.new(id=idx, title=first_name, isactive=1)))
        else:
            markup.row(InlineKeyboardButton(f"❌ {first_name} - {first_price} грн.", callback_data=additeve_cb.new(id=idx, title=first_name, isactive=0)))
    # [InlineKeyboardButton(f"{name} - {price} гривен", callback_data=additeve_cb.new(title=name, isactive=0)) for name, price in additevs.items]

    back_btn = InlineKeyboardButton('➖️', callback_data=product_cb.new(id=idx, action='decrease'))
    count_btn = InlineKeyboardButton(count, callback_data=product_cb.new(id=idx, action='count'))
    next_btn = InlineKeyboardButton('➕️', callback_data=product_cb.new(id=idx, action='increase'))
    markup.row(back_btn, count_btn, next_btn)

    return markup