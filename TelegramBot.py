from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

import requests
import datetime
date = datetime.date.today()

from config import TELEGRAM_TOKEN, yandex_token, from_code, to_code


def get_subtrain_data(from_station, to_station, date, next_hours=2):
    current_time = str(datetime.datetime.now().time())[:5]
    current_minutes = int(current_time[:2])*60 + int(current_time[3:])

    req = requests.get(f'https://api.rasp.yandex.net/v3.0/search/?'
                            f'apikey={yandex_token}'
                            f'&from={from_station}'
                            f'&to={to_station}'
                            f'&date={date}'
                            )
    print(req.status_code)
    print(current_time)
    response_text = req.json()
    nearby_counter = 0
    answer = ''
    segments = response_text['segments']
    for i in range(len(segments)):
        train = segments[i]
        departure_time = train['departure'][11:16]
        departure_minutes = int(departure_time[:2])*60 + int(departure_time[3:])
        arrival_time = train['arrival'][11:16]
        transport_type = train['thread']['transport_subtype']['title'][:11]
        if departure_minutes < current_minutes:
            continue
        if 0 <= departure_minutes - current_minutes <= next_hours * 60:
            answer += f'{departure_time} {arrival_time} {transport_type}\n'
        else:
            if len(answer) == 0:
                answer = f'На ближайшие {next_hours} часа рейсов нет'
            break
    if answer:
        return answer
    else:
        return 'answer is empty'


bot = Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot)
button_2hours = types.KeyboardButton('Ближайшие 2 часа')
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(button_2hours)


async def send_msg(id, answr):
    try:
        await bot.send_message(id, answr)
    except:
        await bot.send_message(id, 'Неизвестная ошибка!')


@dispatcher.message_handler(commands=['start'])
async def start(message: types.Message):
    await bot.send_message(message.from_user.id, 'Привет! давай посмотрим электрички!',
                           reply_markup=keyboard)
    print('1')
    answr = get_subtrain_data(from_code, to_code, date)
    await send_msg(message.from_user.id, answr)


@dispatcher.message_handler()
async def bot_message(message: types.Message):
    if message.text == 'Ближайшие 2 часа':
        answr = get_subtrain_data(from_code, to_code, date)
        await send_msg(message.from_user.id, answr)
    else:
        await bot.send_message(message.from_user.id, 'Неизвестная команда')

if __name__ == '__main__':
    executor.start_polling(dispatcher)


#somechanges