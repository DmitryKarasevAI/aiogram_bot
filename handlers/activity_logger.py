from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from config import WEATHER_API_TOKEN
from storage import users
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
async def start_form(message: Message, command: CommandObject):
    amount = int(command.args)
    users[message.from_user.id]["logged_water"] += amount
    curr_amount = users[message.from_user.id]["logged_water"]
    total_amount = users[message.from_user.id]["water_goal"]
    await message.reply(
        f"Вы выпили {amount} мл. воды\n"
        f"Суммарно за сегодня Вы выпили {curr_amount}/{total_amount} мл."
    )


# Функция для подключения обработчиков
def include_logging_router(dp):
    dp.include_router(router)
