import io
import matplotlib.pyplot as plt
from aiogram import Router
from aiogram.types import Message, BufferedInputFile
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
            users[message.from_user.id]['water_progress'].append(curr_amount)
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
    users[message.from_user.id]['calorie_progress'].append(users[message.from_user.id]['logged_calories'])
    await message.reply(f"Записано: {calories} ккал.")
    await state.clear()


@router.message(Command("log_workout"))
async def log_workout(message: Message, command: CommandObject):
    if message.from_user.id not in users.keys():
        await message.reply(
            "Сначала создайте профиль!"
        )
        return

    if not command.args:
        await message.reply("Введите тип тренировки и время.")
        return

    args = command.args.split()

    if len(args) != 2:
        await message.answer("Введите тип тренировки и время.")
        return

    workout_type, time = args
    async with Translator() as translator:
        workout_type_eng = (await translator.translate(workout_type, src='ru', dest='en')).text

    url = "https://trackapi.nutritionix.com/v2/natural/exercise"
    headers = {
        "Content-Type": "application/json",
        "x-app-id": NUTRITION_API_ID,
        "x-app-key": NUTRITION_API_KEY
    }

    query = ' '.join([workout_type_eng, time, "minutes"])

    payload = {
        "query": query
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(payload)) as response:
            print(f"Status: {response.status}")
            response_json = await response.json()

    if response.status == 200:
        workout_type_response = response_json['exercises'][0]['name']
        async with Translator() as translator:
            workout_type_response_ru = (await translator.translate(workout_type_response, src='en', dest='ru')).text
        calories_burnt = response_json['exercises'][0]['nf_calories']
        extra_water = 200 * (int(time) // 30)
        users[message.from_user.id]['burnt_calories'] += calories_burnt
        if extra_water:
            await message.reply(
                f"{workout_type_response_ru.capitalize()} {time} минут — {calories_burnt} ккал.\n"
                f"Дополнительно: выпейте {extra_water} мл воды."
            )
        else:
            await message.reply(
                f"{workout_type_response_ru.capitalize()} {time} минут — {calories_burnt} ккал."
            )
    else:
        await message.reply(
            f"Я не понимаю, что такое {workout_type.capitalize()} :("
        )


@router.message(Command("check_progress"))
async def check_progress(message: Message):
    if message.from_user.id not in users.keys():
        await message.reply(
            "Сначала создайте профиль!"
        )
    else:
        user_data = users[message.from_user.id]
        consumed_water = user_data["logged_water"]
        target_water = user_data["water_goal"]
        consumed_calories = user_data["logged_calories"]
        target_calories = user_data["calorie_goal"]
        burnt_calories = user_data["burnt_calories"]
        await message.reply(
            "Прогресс:\n"
            "Вода:\n"
            f"- Выпито: {consumed_water} мл из {target_water} мл.\n"
            f"- Осталось: {target_water - consumed_water} мл.\n"

            "Калории:\n"
            f"- Потреблено: {consumed_calories} ккал из {target_calories} ккал.\n"
            f"- Сожжено: {burnt_calories} ккал.\n"
            f"- Баланс: {round(consumed_calories - burnt_calories, 2)} ккал.\n"
        )


@router.message(Command("water_graph"))
async def water_graph(message: Message):
    if message.from_user.id not in users.keys():
        await message.reply(
            "Сначала создайте профиль!"
        )
    else:
        user_data = users[message.from_user.id]
        water_progress = user_data["water_progress"]
        water_goal = user_data["water_goal"]
        plt.figure(figsize=(4, 3))
        plt.plot([i for i in range(len(water_progress))], water_progress, marker='o')
        plt.axhline(y=water_goal, color='red', linestyle='--', linewidth=2)
        plt.title("График потребления воды")
        plt.xlabel("Ваши замеры")
        plt.ylabel("Потреблено воды (мл.)")

        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)

        plt.close()

        plot_bytes = buffer.getvalue()

        image_file = BufferedInputFile(
            file=plot_bytes,
            filename="plot.png"
        )

        await message.answer_photo(
                photo=image_file,
                caption="Ваше потребление воды"
            )


# Функция для подключения обработчиков
def include_logging_router(dp):
    dp.include_router(router)
