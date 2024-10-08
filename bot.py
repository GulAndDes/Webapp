from aiogram import Bot, Dispatcher, executor, types  # type: ignore
from aiogram.types.web_app_info import WebAppInfo  # type: ignore
import requests  # type: ignore

bot = Bot("7131551862:AAGAr2yc-vfSBvSg7M0FZ8wRwGHoSutMXhc")
dp = Dispatcher(bot)


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup()
    markup.add(
        types.KeyboardButton(
            "Открыть сайт", web_app=WebAppInfo(url="http://127.0.0.1/")
        )
    )
    await message.answer("Кнопку жми, лошок.", reply_markup=markup)


@dp.message_handler(commands=["register"])
async def register(message: types.Message):
    username = "your_username"  # Replace with actual user input
    password = "your_password"  # Replace with actual user input

    response = requests.post(
        "http://127.0.0.1/register",
        json={"username": username, "password": password},
    )
    await message.answer(response.json().get("message", "Something went wrong"))


@dp.message_handler(commands=["login"])
async def login(message: types.Message):
    username = "your_username"  # Replace with actual user input
    password = "your_password"  # Replace with actual user input

    response = requests.post(
        "http://127.0.0.1/login", json={"username": username, "password": password}
    )
    await message.answer(response.json().get("message", "Something went wrong"))


executor.start_polling(dp)
