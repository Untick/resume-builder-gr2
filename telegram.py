import datetime
from typing import Callable, Union

from telebot import TeleBot, types
from telebot.apihelper import ApiTelegramException

import config
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

import crud
import utils

bot = TeleBot(token=config.TG_BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start_command(message: types.Message):
    user_info_id, user_info_name = crud.get_user_by_tg_id(message.from_user.username)
    if user_info_id:
        other_message_handler(message)
    else:
        msg = 'Пользователь не обнаружен'
        bot.reply_to(message, msg)


@bot.message_handler(commands=['help'])
def help_command(message: types.Message):
    user_info_id, user_info_name = crud.get_user_by_tg_id(message.from_user.username)
    if user_info_id:
        msg = '''Команды бота:
/menu - показать меню
/help - показать эту справку'''
    else:
        msg = 'Пользователь не обнаружен'
    bot.reply_to(message, msg)


@bot.message_handler(commands=['menu'])
async def menu_command_tg(message: types.Message):
    user_info_id, user_info_name = crud.get_user_by_tg_id(message.from_user.username)
    if user_info_id:
        UserMenu.get_menu(user_info_id).cb_main_menu.set_active(jump=True)


# общий обработчик команд
@bot.message_handler(content_types=['text'])
def other_message_handler(message: types.Message):
    user_info_id, user_info_name = crud.get_user_by_tg_id(message.from_user.username)
    if not user_info_id:
        bot.reply_to(message, 'Пользователь не обнаружен')
        return
    user_answer = message.text  # еще есть html_text и разные типы сообщения - пока это все не обрабатываем, только простой текст из текстового сообщения
    if user_answer.lower().strip() == 'stop':
        return

    if user_answer.startswith("/"):
        msg = 'Команда не найдена, /help для помощи'
        bot.send_message(message.from_user.id, msg)
    else:
        (current_user_input_handler or reply_stub)(message, user_answer)


@bot.message_handler(content_types=['voice'])
def voice_message(message):
    voice = message.voice
    file_info = bot.get_file(voice.file_id)
    file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'
    start = datetime.datetime.now().timestamp()
    transcription = utils.get_text_from_audio(file_url)
    bot.send_message(message.chat.id, f'Результат распознавания ({datetime.datetime.now().timestamp() - start:.1f}): {transcription}')
    (current_user_input_handler or reply_stub)(message, transcription)


@bot.callback_query_handler(func=lambda call: call.data.startswith(menu_prefix))
def button_callback(call: CallbackQuery):
    user_menu = UserMenu.get_menu(call.from_user.id)
    if not user_menu.menu_message_handler or user_menu.menu_message_handler.id != call.message.id:
        bot.delete_message(call.message.chat.id, call.message.id)
    user_menu.menu_screen[call.data].set_active()


def chat_gpt_reply_to_user_message(message, user_answer):
    bot.send_chat_action(message.from_user.id, 'typing')
    next_question = utils.handle_user_reply(message.from_user.username, user_answer)
    if next_question:
        bot.send_message(message.from_user.id, next_question)


def reply_stub(message, _):
    bot.send_message(message.from_user.id, f"В настоящий момент я не понимаю, к чему относится эта информация - выберите команду из меню")


def get_emoji_for_number(number):
    if 1 <= number <= 10:
        unicode_code_point = ord('1') + (number - 1)
        return chr(unicode_code_point) + '\uFE0F\u20E3'
    else:
        res = ""
        for n in str(number):
            res += get_emoji_for_number(int(n))
        return res


current_user_input_handler = None
menu_prefix = "menu-"


class UserMenu:
    users = {}

    def __init__(self, user_id):
        self.user_id = user_id
        if user_id in UserMenu.users:
            raise IndexError(f"User {user_id} already exists")
        self.menu_screen = {}
        self.menu_message_handler = None
        UserMenu.users[self.user_id] = self

        self.cbs_job = []

        self.cb_main_menu = Screen(self, "back", "⬅️ Назад", "Выберите раздел Общей информации для редактирования", reply_stub)
        cb_main_menu = self.cb_main_menu

        cb_common_info = Screen(self, "ci", "ℹ️ Общая информация", "Выберите место работы для редактирования или добавьте новое", reply_stub)
        cb_common_info_last_name = Screen(self, "ci_last_name", "Фамилия", "Укажите свое фамилию в именительном падеже", self.get_reply_handler("Фамилия"))
        cb_common_info_first_name = Screen(self, "ci_first_name", "Имя", "Укажите свое имя в именительном падеже", self.get_reply_handler("Имя"))
        cb_common_info_surname = Screen(self, "ci_surname", "Отчество", "Укажите свое отчество в именительном падеже", self.get_reply_handler("Отчество"))
        cb_common_info_sex = Screen(self, "ci_sex", "Пол", "Укажите свой пол", self.get_reply_handler("Пол"))
        cb_common_info_birth_date = Screen(self, "ci_birth_date", "Дата рождения", "Укажите дату своего рождения", self.get_reply_handler("Дата рождения"))

        self.cb_jobs = Screen(self, "jobs", "💼 Опыт работы", "Выберите раздел для редактирования", reply_stub)
        cb_jobs = self.cb_jobs
        self.cb_add_job = Screen(self, "jobs_add", "➕ Добавить место работы", "Укажите место работы, вашу роль и опыт работы", self.add_job_handler)
        cb_add_job = self.cb_add_job
        cb_covering_letter = Screen(self, "cl", "✉️ Сопроводительное письмо", "Пришлите текст сопроводительного письма", self.get_reply_handler("Сопроводительное письмо"))

        cb_main_menu.set_keyboard([cb_common_info, cb_jobs, cb_covering_letter])
        cb_common_info.set_keyboard([cb_common_info_last_name, cb_common_info_first_name, cb_common_info_surname, cb_common_info_sex, cb_common_info_birth_date, cb_main_menu])
        cb_jobs.set_keyboard([cb_add_job, cb_main_menu])
        Screen.set_default_keyboard(UserMenu.users[self.user_id], [cb_main_menu])

        cb_main_menu.set_active()

    def get_reply_handler(self, field_name):
        def input_covering_letter(message, text):
            bot.send_message(message.from_user.id, f'Вы указали для поля "{field_name}" следующий текст:\n{text}')
            self.cb_main_menu.set_active(jump=True)

        return input_covering_letter

    def add_job_handler(self, message, text, replace=None):
        job_num = replace or len(self.cbs_job) + 1

        def input_edit_job(new_message, new_text):
            bot.send_message(message.from_user.id, f'Вы изменили описание места работы. Старое описание\n{text}\n\nНовое описание:\n{new_text}')
            self.add_job_handler(new_message, new_text, job_num)

        if replace:
            self.cbs_job[job_num - 1].unregister()

        cb_jobs_new_job = Screen(self, f"jobs_{job_num}", f"{get_emoji_for_number(job_num)} {text}", f'Укажите исправленную информацию для места работы:\n{text}', input_edit_job)

        if replace:
            self.cbs_job[job_num - 1] = cb_jobs_new_job
        else:
            self.cbs_job.append(cb_jobs_new_job)

        self.cb_jobs.set_keyboard(self.cbs_job + [self.cb_add_job, self.cb_main_menu])

        if not replace:
            bot.send_message(message.from_user.id, f'Вы добавили следующий опыт работы:\n{text}')
        self.cb_jobs.set_active(jump=True)

    @classmethod
    def get_menu(cls, user_id):
        if user_id not in UserMenu.users:
            UserMenu.users[user_id] = UserMenu(user_id)
        return UserMenu.users[user_id]


class Screen:
    def __init__(self, user_menu: UserMenu, id: str, button_text: str, message_text: Union[str, Callable], input_handler: Callable):
        self.id = f"{menu_prefix}{user_menu.user_id}-{id}"
        self.user_menu = user_menu

        if self.id in self.user_menu.menu_screen:
            raise IndexError(f"Id {id} already exists")
        self.user_menu.menu_screen[self.id] = self
        self.button_text = button_text
        self.message_text = message_text
        self.reply_markup = None
        self.input_handler = input_handler

    def unregister(self):
        del self.user_menu.menu_screen[self.id]

    @staticmethod
    def set_default_keyboard(user_menu: UserMenu, buttons: list):
        for id in user_menu.menu_screen:
            instance = user_menu.menu_screen[id]
            if not instance.reply_markup:
                instance.set_keyboard(buttons)

    def set_keyboard(self, buttons: list):
        keyboard = []
        for button in buttons:
            keyboard.append([InlineKeyboardButton(text=button.button_text, callback_data=button.id)])
        self.reply_markup = InlineKeyboardMarkup(keyboard)

    def set_active(self, jump=False):
        global current_user_input_handler
        current_user_input_handler = self.input_handler
        text = self.message_text if isinstance(self.message_text, str) else self.message_text(self)
        if jump and self.user_menu.menu_message_handler:
            try:
                bot.delete_message(self.user_menu.menu_message_handler.chat.id, self.user_menu.menu_message_handler.id)
            except ApiTelegramException:
                pass
            self.user_menu.menu_message_handler = None
        if self.user_menu.menu_message_handler:
            if self.user_menu.menu_message_handler.text == text:
                if self.user_menu.menu_message_handler.reply_markup:
                    # кнопки в новом наборе пересозданы, сравнение в лоб не сработает, поэтому всегда сначала удаляем, потом ставим новые
                    bot.edit_message_reply_markup(self.user_menu.menu_message_handler.chat.id, self.user_menu.menu_message_handler.id, reply_markup=None)
                bot.edit_message_reply_markup(self.user_menu.menu_message_handler.chat.id, self.user_menu.menu_message_handler.id, reply_markup=self.reply_markup)
            else:
                self.user_menu.menu_message_handler = bot.edit_message_text(text, self.user_menu.menu_message_handler.chat.id, self.user_menu.menu_message_handler.id, parse_mode='HTML', reply_markup=self.reply_markup)
        else:
            self.user_menu.menu_message_handler = bot.send_message(self.user_menu.user_id, text, reply_markup=self.reply_markup)


print("Бот запущен")
bot.infinity_polling()
