from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging
from config import WEATHER_API_TOKEN
from states import SetUpForm
from storage import users
import aiohttp

router = Router()


@router.message(Command("set_profile"))
async def start_form(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(SetUpForm.weight)


@router.message(SetUpForm.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=float(message.text))
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(SetUpForm.height)


@router.message(SetUpForm.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=int(message.text))
    await message.reply("Введите ваш возраст:")
    await state.set_state(SetUpForm.age)


@router.message(SetUpForm.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.reply("Введите ваш пол (М/Ж):")
    await state.set_state(SetUpForm.sex)


@router.message(SetUpForm.sex)
async def process_sex(message: Message, state: FSMContext):
    await state.update_data(sex=message.text)
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(SetUpForm.active_time)


@router.message(SetUpForm.active_time)
async def process_active_time(message: Message, state: FSMContext):
    await state.update_data(active_time=int(message.text))
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(SetUpForm.city)


@router.message(SetUpForm.city)
async def process_city(message: Message, state: FSMContext):
    data = await state.get_data()
    weight = data.get("weight")
    height = data.get("height")
    age = data.get("age")
    sex = data.get("sex")
    active_time = data.get("active_time")
    city = data.get("city")

    coord_url = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit={1}&appid={WEATHER_API_TOKEN}'

    async with aiohttp.ClientSession() as session:
        async with session.get(coord_url) as response:
            data = (await response.json())[0]
            lon, lat = data['lon'], data['lat']

    temp_url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_TOKEN}'
    async with aiohttp.ClientSession() as session:
        async with session.get(temp_url) as response:
            temp = (await response.json())["main"]["temp"] - 273.15

    water_goal = int(round(30 * weight + 500 * (active_time // 30) + 500 * (temp > 25), -2))

    # По формуле Миффлина — Сан Жеора:
    calorie_goal = int(round(10 * weight + 6.25 * height - 5 * age + 5 * (sex == 'М') - 161 * (sex == 'Ж')))

    logging.info(f'{data}, {lon}, {lat}, {temp}')

    # Меняем параметры user по его id:
    users[message.from_user.id] = {
        "weight": weight,
        "height": height,
        "age": age,
        "activity": active_time,
        "city": city,
        "water_goal": water_goal,
        "calorie_goal": calorie_goal,
        "logged_water": 0,
        "logged_calories": 0,
        "burned_calories": 0
    }

    await message.reply(
        f"Ваша цель по калориям: {calorie_goal}\n"
        f"Ваша цель по воде: {water_goal}\n"
    )

    await state.clear()


# Функция для подключения обработчиков
def include_profile_router(dp):
    dp.include_router(router)
