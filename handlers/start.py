from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")


# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/help - Выводит список команд\n"
        "/set_profile - Настройка профиля\n"
        "/log_water <количество> - Сохраняет, сколько воды выпито\n"
        "/log_food <название продукта> - Сохраняет калорийность\n"
        "/log_workout <тип тренировки> <время (мин)> - Фиксирует сожжённые калории\n"
        "/check_progress - Показывает прогресс по целям за день\n"
        "/water_graph - Показывает график потребления воды\n"
        "/calorie_graph - Показывает график потребления ккал.\n"
    )


# Функция для подключения обработчиков
def include_start_router(dp):
    dp.include_router(router)
