import datetime

from pyrogram.storage import MemoryStorage
from telebot import TeleBot, types


import config
import crud
import utils

bot = TeleBot(token=config.TG_BOT_TOKEN)
# storage = MemoryStorage()


@bot.message_handler(commands=['start'])
def start_command(message: types.Message):
    data = crud.get_user_by_tg_id(message.from_user.username)
    if data:
        other_message_handler(message)
    else:
        msg = 'Пользователь не обнаружен'
        bot.reply_to(message, msg)


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
@bot.message_handler(content_types=['text'])
def other_message_handler(message: types.Message):
    user_info_id, user_info_name = crud.get_user_by_tg_id(message.from_user.username)
    if not user_info_id:
        bot.reply_to(message, 'Пользователь не обнаружен')
        return
    user_answer = message.text  # еще есть html_text и разные типы сообщения - пока это все не обрабатываем, только простой текст
    if user_answer.lower().strip() == 'stop':
        return

    if user_answer == "/start":
        user_answer = "Привет!"

    if user_answer.startswith("/"):
        msg = 'Команда не найдена, /help для помощи'
        bot.send_message(message.from_user.id, msg)
    else:
        reply_to_user_message(message, user_answer)


@bot.message_handler(content_types=['voice'])
def voice_message(message):
    voice = message.voice
    file_info = bot.get_file(voice.file_id)
    file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'
    start = datetime.datetime.now().timestamp()
    transcription = utils.get_text_from_audio(file_url)
    bot.send_message(message.chat.id, f'Результат распознавания ({datetime.datetime.now().timestamp()-start:.1f}): {transcription}')
    reply_to_user_message(message, transcription)


def reply_to_user_message(message, user_answer):
    bot.send_chat_action(message.from_user.id, 'typing')
    next_question = utils.handle_user_reply(message.from_user.username, user_answer)
    if next_question:
        bot.send_message(message.from_user.id, next_question)
