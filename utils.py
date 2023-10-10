import os

import requests
from fastapi import HTTPException
from starlette.responses import RedirectResponse
import whisper

import auth
import chatgpt
import config
import crud


# проверка авторизации, получение данных пользователя
def get_user_auth(request):
    # получение jwt-токена
    jwt_token = request.cookies.get('token')
    data = auth.verify_jwt_token(jwt_token)

    # получение имени пользователя
    user_id = None
    username = None
    if data:
        user_id = data['id'] if 'id' in data else None
        username = data['user'] if 'user' in data else None

        # аутентификация пользователя
        user = crud.get_user_by_name(username)
        if not user:
            user_id = None
            username = None

    return user_id, username


# создание и сохранение токена в cookies, создание перенаправления
def get_redirect(url, data: dict):
    # создаём jwt-токен
    jwt_token = auth.create_jwt_token(data)

    # создаём перенаправление с установкой cookies
    response = RedirectResponse(url)
    response.set_cookie(key='token', value=jwt_token)
    return response


def get_appform_info_str(data, fields: dict, caption: str) -> str:
    if not any(key in data for key in fields):
        return ''

    ret = ''
    for key, value in fields.items():
        if key not in data:
            continue
        if not data[key]:
            continue
        value = value + ': ' if value else ''
        ret += value + data[key] + """
"""

    if not ret:
        return ''
    ret = f"""<b>{caption}</b>
{ret}
"""
    return ret


def get_appform_info_bool(data, fields: dict, addition: str, caption: str) -> str:
    if not any(key in data for key in fields):
        return ''
    ret = ''
    lst = []
    for key, value in fields.items():
        print(key, value, data[key])
        if key not in data:
            continue
        if data[key]:
            lst.append(value)

    lst = ', '.join(lst) + (f", {data[addition]}" if addition in data else '')
    if lst:
        ret = f"""<b>{caption}</b>
{lst}

"""
    return ret


# выдача анкеты пользователя в тг-бот
def format_appform_tg(data):
    # личная информация
    dc = {'name': 'Имя', 'birthdate': 'Дата рождения', 'city': 'Город'}
    ret = get_appform_info_str(data, dc, 'Личные данные')

    # контакты
    dc = {'phone': 'Телефон', 'email': 'email', 'telegram': 'Telegram'}
    ret += get_appform_info_str(data, dc, 'Контакты')

    # навыки (в будущем надо переделать, пока тестовый вариант)
    # TODO: вынести все навыки с названиями и значениями id для html в отдельную таблицу и получать данные оттуда
    dc = {
        'skillPython': 'Python', 'skillNumPy': 'NumPy', 'skillPandas': 'Pandas', 'skillMatplotlib': 'Matplotlib',
        'skillSeaborn': 'Seaborn', 'skillKeras': 'Keras', 'skillPytorch': 'Pytorch', 'skillTensorflow': 'Tensorflow',
        'skillNLP': 'NLP', 'skillGPT': 'GPT', 'skillObjectDetection': 'Object Detection'
    }
    ret += get_appform_info_bool(data, dc, 'customSkills', 'Навыки')

    # образование
    dc = {'education': ''}
    ret += get_appform_info_str(data, dc, 'Образование')

    # опыт работы
    dc = {'experience': ''}
    ret += get_appform_info_str(data, dc, 'Опыт работы')

    # пройденные в УИИ курсы
    dc = {'courseDataScience': 'Data Science', 'coursePython': 'Python разработчик'}
    ret += get_appform_info_bool(data, dc, '', 'Курсы УИИ')

    return ret


# проверка входящих данных в post-запросе
def check_tg_api_data(data):
    # проверка токена
    if data.token != config.TG_API_TOKEN:
        raise HTTPException(status_code=400, detail='Token required')

    # проверка имени пользователя
    if not data.username:
        raise HTTPException(status_code=400, detail='Required field is missing')

    return True


# обработка команды /form в тг-боте
async def form_command(username: str):
    data = crud.get_user_by_tg_id(username)
    if data:
        user_id = data[0]
        form_data = crud.get_appform(user_id)

        if form_data:
            msg = format_appform_tg(form_data)
            if not msg:
                msg = 'Пустая анкета'
        else:
            msg = 'Ошибка анкеты пользователя'
    else:
        msg = 'Пользователь не обнаружен'

    return msg


# обработка команды /resume в тг-боте
async def resume_command(username: str):
    data = crud.get_user_by_tg_id(username)
    if data:
        user_id = data[0]
        msg = crud.get_resume(user_id)
        if not msg:
            msg = 'Резюме ещё не сформировано'
    else:
        msg = 'Пользователь не обнаружен'

    return msg


# обработка команды /generate в тг-боте
async def generate_command(username: str):
    data = crud.get_user_by_tg_id(username)
    if data:
        user_id = data[0]
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

    return msg


def handle_user_reply(username, user_answer):
    data = crud.get_user_by_tg_id(username)
    if data:
        user_id = data[0]
        chatgpt.gpt_set_user_answer(user_id, user_answer)
        return chatgpt.gpt_get_hr_question(user_id)


def get_text_from_audio(file_url: str):
    response = requests.get(file_url)

    audio_file_path = file_url.split("/")[-1]  # Выберите подходящее имя и формат файла
    with open(audio_file_path, 'wb') as file:
        file.write(response.content)

    transcription = transcribe_wisper(audio_file_path, True)
    print(transcription)

    os.remove(audio_file_path)

    return transcription


# Size	Parameters	English-only model	Multilingual model	Required VRAM	Relative speed
# tiny      39 M    tiny.en 	tiny	~1 GB	~32x
# base      74 M	base.en	    base	~1 GB	~16x
# small     244 M	small.en	small	~2 GB	~6x
# medium    769 M	medium.en	medium	~5 GB	~2x
# large     1550 M  N/A	        large	~10 GB	1x
# на практике качество small - неудовлетворительное - не распознает термины
# качество medium приемлемое, но время на CPU - нет, в 5 раз медленнее реального времени записи
# кроме питоновских библиотек в системе должен быть установлен ffmpeg
transcribe_model = whisper.load_model("medium")


def transcribe_wisper(audio_file_path, proceed_local=False):
    if proceed_local:
        result = transcribe_model.transcribe(audio_file_path, fp16=False)
        transcription = result["text"]
    else:
        url = 'https://api.openai.com/v1/audio/transcriptions'
        headers = {
            'Authorization': f'Bearer {config.OPENAI_API_KEY}',
        }

        response = requests.post(
            url,
            headers=headers,
            files={'file': ('audio.ogg', open(audio_file_path, 'rb'))},
            data={'model': 'whisper-1'}  # Указываем модель (в данном случае, whisper-1)
        )

        if response.status_code == 200:
            result = response.json()
            transcription = result['text']
        else:
            print(f'Ошибка: {response.status_code}')
            print(response.text)
            return None

    return transcription
