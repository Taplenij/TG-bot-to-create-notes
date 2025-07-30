import asyncpg.exceptions
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta, time
import app.requests as rq

import app.keyboards as kb

import asyncio

request_com = rq.DBC()

router = Router()


class Reg(StatesGroup):
    new_note = State()
    remove_note = State()
    change_note = State()
    check_note = State()


@router.message(Command('start'))  # Start the bot
async def start_fun(message: Message):
    await message.answer('Привет!😊\n Я - бот для напоминания о необходимых задачах,'
                         ' которые можно настроить по времени выполнения.🔖', reply_markup=kb.start_keyw)
    await request_com.initialize_pool()
    await request_com.record_id(message.from_user.id)  # Do query


@router.message(F.text.lower() == 'сосал?')  # Sexy secret
async def sosal(message: Message):
    await message.reply('Да')


@router.callback_query(F.data == 'add')
async def add(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Новая заметка')
    await callback.message.answer('Укажите номер задачи, задачу и время напоминания в формате num;task;hours;minute.'
                                  '\nНапример: 1;Купить водички килограмм;19;55')
    await state.set_state(Reg.new_note)


async def wait_func(hour, minute, task, message: Message):  # Initialize sending notification
    await request_com.initialize_pool()
    active_tasks = await request_com.get_info(message.from_user.id)  # Это не ГЭПЭТЭ писал :(
    now = datetime.now()
    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_time < now:  # If time that was in the moment of sending message less than specified ...
        target_time += timedelta(days=1)  # ...go to the next day
    wait_time = (target_time - now).total_seconds()  # Create time waiting
    await asyncio.sleep(wait_time)
    if task in active_tasks:  # If exists...
        await message.answer(f'Напоминание: {task}')  # ...send notification
        await request_com.remove_rec(task)
    else:
        pass


@router.message(Reg.new_note)
async def first_step(message: Message, state: FSMContext):
    await request_com.initialize_pool()
    active_tasks = await request_com.get_info(message.from_user.id)
    task_info = message.text.split(';')
    num = int(task_info[0])
    task = task_info[1]
    time_s = time(hour=int(task_info[2]), minute=int(task_info[3]))
    if task in active_tasks or len(task_info) < 4:
        await message.answer('Ой!😢 Произошла ошибка.'
                             ' Возможно, вы предоставили недостаточно данных либо ввели уже существующую заметку')
        await state.clear()
    try:
        await request_com.binding_note(task, time_s, message.from_user.id, num)
    except asyncpg.exceptions.PostgresSyntaxError:
        print('Ошибка запроса')
    await state.update_data(new_note=task_info)
    await message.answer(f'Отлично!👌 Ваша заметка {task} была записана и даст о себе знать в {time_s}')
    await state.clear()
    hour = int(task_info[2])
    minute = int(task_info[3])
    await wait_func(hour, minute, task, message)


@router.callback_query(F.data == 'del')
async def delete_note(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Удалить заметку')
    await callback.message.answer('Укажите номер заметки, которую хотите удалить')
    await state.set_state(Reg.remove_note)


@router.message(Reg.remove_note)
async def second_step(message: Message, state: FSMContext):
    try:
        await request_com.initialize_pool()
        need_to_rem = int(message.text)
        del_task = await request_com.get_info(message.from_user.id, need_to_rem)
        active_tasks = await request_com.get_info(message.from_user.id)
        if not del_task:
            await message.answer('Такой заметки не существует😞')
            await state.set_state(Reg.remove_note)
        else:
            await request_com.remove_rec(del_task[0])
            await message.answer(f'Заметка \'{del_task[0]}\' была удалена')
            await request_com.change_num_id(message.from_user.id, active_tasks)
            await state.clear()
    except ValueError:
        await message.answer('Номер заметки должен быть числом')
        await state.set_state(Reg.remove_note)


@router.callback_query(F.data == 'check')
async def check_notes(callback: CallbackQuery, state: FSMContext):
    await request_com.initialize_pool()
    await callback.answer('Просмотреть мои заметки')
    tasks_info = await request_com.get_full_info(callback.from_user.id)
    if not tasks_info:
        await callback.message.answer('У вас пока нет заметок')
    else:
        await callback.message.answer('Ваши заметки:')
        for task in tasks_info:
            await callback.message.answer('|'.join(map(str, task)))


@router.callback_query(F.data == 'change')
async def change_note(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Изменить мои заметки')
    await callback.message.answer('Введите номер заметки, которую хотите изменить и новую заметку(1;new_note)')
    await state.set_state(Reg.change_note)


@router.message(Reg.change_note)
async def third_step(message: Message, state: FSMContext):
    await request_com.initialize_pool()
    new_note_info = message.text.split(';')
    await request_com.change(message.from_user.id, int(new_note_info[0]), new_note_info[1])
    await message.answer(f'Готово! Заметка под номером {new_note_info[0]} соответствует {new_note_info[1]}')
    await state.clear()
