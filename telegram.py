import os

from pyrogram.storage import MemoryStorage
from telebot import TeleBot, types


import config
import crud
import utils


bot = TeleBot(token=config.TG_BOT_TOKEN)
#storage = MemoryStorage()

# обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    if data:
        msg = 'Добро пожаловать, ' + data[1]
    else:
        msg = 'Пользователь не обнаружен'
    bot.reply_to(message, msg)


# обработчик команды /help
@bot.message_handler(commands=['help'])
def help_command(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    if data:
        msg = '''Команды бота:
/form - показать анкетные данные,
/resume - показать сгенерированное резюме
/generate - сгенерировать новое резюме'''
    else:
        msg = 'Пользователь не обнаружен'
    bot.reply_to(message, msg)


# обработчик команды /form
@bot.message_handler(commands=['form'])
def form_command_tg(message: types.Message):
    msg = utils.form_command(message.from_user.username)
    bot.reply_to(message, msg, parse_mode='HTML')


# обработчик команды /resume (вывод сформированного резюме)
@bot.message_handler(commands=['resume'])
def resume_command_tg(message: types.Message):
    msg = utils.resume_command(message.from_user.username)
    bot.reply_to(message, msg)


# обработчик команды /generate
@bot.message_handler(commands=['generate'])
async def generate_command_tg(message: types.Message):
    msg = utils.generate_command(message.from_user.username)
    bot.reply_to(message, msg)


# общий обработчик команд
@bot.message_handler()
async def echo_message(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    if not data:
        bot.reply_to(message, 'Пользователь не обнаружен')
        return

    msg = 'Команда не найдена, /help для помощи'
    bot.send_message(message.from_user.id, msg)
