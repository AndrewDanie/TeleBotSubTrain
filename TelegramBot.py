import datetime

from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

import requests
from datetime import timedelta
import pytz

from config import TELEGRAM_TOKEN, yandex_token

home = 'Пет'
city = 'СПб'
msg = {
    '2h_pet': f'Ближайшие 2 часа({home})',
    '2h_bal': f'Ближайшие 2 часа({city})',
    'tday_pet': f'Сегодня({home})',
    'tday_bal': f'Сегодня({city})',
    'tmr_pet': f'Завтра({home})',
    'tmr_bal': f'Завтра({city})',
}


def get_subtrain_data(msg_date, key=msg['2h_pet']):

    segments = get_data_from_yandex_API(key, msg_date)
    return form_answer(segments, msg_date, key)


def get_data_from_yandex_API(key, msg_date):
    date = get_needed_date(msg_date, key)
    from_station, to_station = get_stations_id(key)
    req = requests.get(f'https://api.rasp.yandex.net/v3.0/search/?'
                       f'apikey={yandex_token}'
                       f'&from={from_station}'
                       f'&to={to_station}'
                       f'&date={date}'
                       )
    return req.json()['segments']


def get_stations_id(key):
    from config import petr_code, balt_code
    if key == '2h_pet' or key == 'tday_pet' or key == 'tmr_pet':
        # print('from Petergof')
        return petr_code, balt_code
    else:
        # print('from SPb')
        return balt_code, petr_code


def get_needed_date(msg_date, key):
    if key == 'tmr_pet' or key == 'tmr_bal':
        next_day = timedelta(days=1)
        return msg_date.date() + next_day
    else:
        return msg_date.date()


def get_needed_time_period(msg_date, key):
    if key == '2h_pet' or key == '2h_bal':
        return 2
    else:
        return 24


def get_current_minute(msg_date, key):
    curr_hour = str(msg_date.time())[:5]
    if key == 'tmr_pet' or key == 'tmr_bal':
        curr_min = 0
    else:
        curr_min = int(curr_hour[:2]) * 60 + int(curr_hour[3:])
    return curr_min


def form_answer(segments, msg_date, key):
    next_hours = get_needed_time_period(msg_date, key)
    curr_min = get_current_minute(msg_date, key)

    answer = f'{msg[key]}:\n\n'
    for train in segments:
        departure_time = train['departure'][11:16]
        departure_minutes = int(departure_time[:2])*60 + int(departure_time[3:])
        arrival_time = train['arrival'][11:16]
        transport_type = train['thread']['transport_subtype']['title'][:11]
        if departure_minutes < curr_min:
            continue
        if 0 <= departure_minutes - curr_min <= next_hours * 60:
            answer += f'{departure_time} {arrival_time} {transport_type}\n'
        else:
            if len(answer) == 0:
                answer = f'На ближайшие {next_hours} часа рейсов нет'
            break
    if answer:
        return answer
    else:
        return 'answer is empty'


timezone = pytz.timezone('Europe/Moscow')
bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot)

buttons = {}
for key in msg:
    buttons[key] = KeyboardButton(msg[key])
keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

keyboard = keyboard.row(msg['2h_pet'], msg['2h_bal'])
keyboard = keyboard.row(msg['tday_pet'], msg['tday_bal'])
keyboard = keyboard.row(msg['tmr_pet'], msg['tmr_bal'])
# for key in msg:
#     keyboard = keyboard.add


async def send_msg(id, answr):
    try:
        await bot.send_message(id, answr)
    except:
        await bot.send_message(id, 'Неизвестная ошибка!')


@dispatcher.message_handler(commands=['start'])
async def start(message: Message):
    await bot.send_message(message.from_user.id,
                           'Привет! давай посмотрим электрички!\n'
                           f'({home}) - из Петергофа\n'
                           f'({city}) - с Балтийского вокзала',
                           reply_markup=keyboard)


@dispatcher.message_handler()
async def bot_message(message: Message):
    answr = None
    for key in msg:
        if message.text == msg[key]:
            date_time = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
            answr = get_subtrain_data(date_time, key=key)

    if answr is None:
        answr ='Неизвестная команда'
    await send_msg(message.from_user.id, answr)


if __name__ == '__main__':
    executor.start_polling(dispatcher)