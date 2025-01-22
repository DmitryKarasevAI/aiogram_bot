from aiogram.fsm.state import State, StatesGroup


class SetUpForm(StatesGroup):
    weight = State()
    height = State()
    age = State()
    sex = State()
    active_time = State()
    city = State()


class FoodLogger(StatesGroup):
    food_name = State()
    cal_100 = State()
