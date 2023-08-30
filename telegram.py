from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import chatgpt
import crud

# Для запуска сервиса fastapi одновременно с telegram-ботом, необходимо:
# 1. установить в коде флаг START_BOT = True
# 2. ввести TG_BOT_TOKEN (токен вашего телеграм-бота)
# 3. запустить ngrok (команда ngrok http <port>, где <port> совпадает с портом fastapi, обычно 8000)
# 4. ввести NGROK_URL (ссылку на временный url выдаёт ngrok при запуске)
#
# Если telegram bot после запуска веб-сервиса не реагирует, следует немного подождать.
# Для запуска ngrok следует зарегистрироваться на ngrok.com, получить token, скачать приложение ngrok.

START_BOT = False  # True для запуска fastapi вместе с тг-ботом
TG_BOT_TOKEN = 'YOUR TOKEN'  # токен тг-бота
NGROK_URL = 'https://fbf0-94-19-240-38.ngrok-free.app'  # url ngrok

WEBHOOK_PATH = f'/bot/{TG_BOT_TOKEN}'
WEBHOOK_URL = NGROK_URL + WEBHOOK_PATH
bot = Bot(token=TG_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot)


# обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    if data:
        msg = 'Добро пожаловать, ' + data[1]
    else:
        msg = 'Пользователь не обнаружен'
    await message.answer(msg)


# обработчик команды /help
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    if data:
        msg = '''Команды бота:
/form - показать анкетные данные,
/resume - показать сгенерированное резюме
/generate - сгенерировать новое резюме'''
    else:
        msg = 'Пользователь не обнаружен'
    await message.answer(msg)


# обработчик команды /form
@dp.message_handler(commands=['form'])
async def form_command(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    if data:
        msg = 'Функция в разработке'
    else:
        msg = 'Пользователь не обнаружен'
    await message.answer(msg)


# обработчик команды /resume
@dp.message_handler(commands=['resume'])
async def resume_command(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    user_id = data[0]

    if data:
        msg = crud.get_resume(user_id)
        if not msg:
            msg = 'Резюме ещё не сформировано'
    else:
        msg = 'Пользователь не обнаружен'
    await message.answer(msg)


# обработчик команды /generate
@dp.message_handler(commands=['generate'])
async def generate_command(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    user_id = data[0]

    if data:
        result = chatgpt.gpt_resume_builder(user_id)
        if result:
            if not crud.save_resume(user_id, ', '.join(result)):
                msg = 'Ошибка сохранения резюме'
            else:
                msg = 'Резюме успешно сгенерировано'
        else:
            msg = 'Ошибка генерации резюме'
    else:
        msg = 'Пользователь не обнаружен'
    await message.answer(msg)


# общий обработчик команд
@dp.message_handler()
async def echo_message(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    if not data:
        await message.answer('Пользователь не обнаружен')
        return

    msg = 'Команда не найдена, /help для помощи'
    await bot.send_message(message.from_user.id, msg)
