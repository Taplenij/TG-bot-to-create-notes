from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           ReplyKeyboardMarkup, KeyboardButton)

start_keyw = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Новая заметка', callback_data='add'),
     InlineKeyboardButton(text='Удалить заметку', callback_data='del')],
    [InlineKeyboardButton(text='Изменить заметку', callback_data='change'),
     InlineKeyboardButton(text='Просмотреть свои заметки', callback_data='check')]
     ])
