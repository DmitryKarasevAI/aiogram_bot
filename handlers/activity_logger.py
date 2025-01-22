from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from config import NUTRITION_API_ID, NUTRITION_API_KEY
from states import FoodLogger
from storage import users
import aiohttp
from googletrans import Translator
import json
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

router = Router()


@router.message(Command("log_water"))
async def log_water(message: Message, command: CommandObject):
    if message.from_user.id not in users.keys():
        await message.reply(
            "Сначала создайте профиль!"
        )
    else:
        try:
            amount = int(command.args)
            users[message.from_user.id]["logged_water"] += amount
            curr_amount = users[message.from_user.id]["logged_water"]
            total_amount = users[message.from_user.id]["water_goal"]
            await message.reply(
                f"Вы выпили {amount} мл. воды\n"
                f"Суммарно за сегодня Вы выпили {curr_amount}/{total_amount} мл."
            )
        except (TypeError, ValueError):
            await message.reply(
                "Введите корректное количество воды в мл."
            )


@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext, command: CommandObject):
    if message.from_user.id not in users.keys():
        await message.reply(
            "Сначала создайте профиль!"
        )
    else:
        food_name = command.args
        if food_name:
            async with Translator() as translator:
                food_name_eng = (await translator.translate(food_name, src='ru', dest='en')).text

            url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
            headers = {
                "Content-Type": "application/json",
                "x-app-id": NUTRITION_API_ID,
                "x-app-key": NUTRITION_API_KEY
            }

            payload = {
                "query": food_name_eng
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=json.dumps(payload)) as response:
                    print(f"Status: {response.status}")
                    response_json = await response.json()

            if response.status == 200:
                portion_cal = response_json['foods'][0]['nf_calories']
                portion_weight = response_json['foods'][0]['serving_weight_grams']
                cal_100 = round(100 * portion_cal / portion_weight, 2)
                await message.reply(
                    f"{food_name.capitalize()} — {cal_100} ккал на 100 г. Сколько грамм вы съели?"
                )
                await state.update_data(food_name=food_name)
                await state.set_state(FoodLogger.food_name)
                await state.update_data(cal_100=cal_100)
                await state.set_state(FoodLogger.cal_100)
            else:
                await message.reply(
                    f"Я не понимаю, что такое {food_name.capitalize()} :("
                )
        else:
            await message.reply(
                    "Введите название продукта."
                )


@router.message(FoodLogger.cal_100)
async def process_food_weight(message: Message, state: FSMContext):
    data = await state.get_data()
    cal_100 = data.get("cal_100")
    grams = float(message.text)
    calories = round(grams / 100 * cal_100, 1)
    users[message.from_user.id]['logged_calories'] += calories
    await message.reply(f"Записано: {calories} ккал.")
    await state.clear()


# Функция для подключения обработчиков
def include_logging_router(dp):
    dp.include_router(router)
