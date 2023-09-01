from starlette.responses import RedirectResponse

import auth
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


def get_appform_info_skills(data, fields: dict, addition: str, caption: str) -> str:
    if not any(key in data for key in fields):
        return ''
    ret = f"""<b>{caption}</b>
    """
    lst = []
    for key, value in fields.items():
        print(key, value, data[key])
        if key not in data:
            continue
        if data[key]:
            lst.append(value)

    lst = ', '.join(lst) + (f", {data[addition]}" if addition in data else '')
    if lst:
        ret = f"""<b>Навыки</b>
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
    dc = {'skillPython': 'Python', 'skillNumPy': 'NumPy', 'skillPandas': 'Pandas', 'skillMatplotlib': 'Matplotlib',
          'skillSeaborn': 'Seaborn', 'skillKeras': 'Keras', 'skillPytorch': 'Pytorch', 'skillTensorflow': 'Tensorflow',
          'skillNLP': 'NLP', 'skillGPT': 'GPT', 'skillObjectDetection': 'Object Detection'}
    ret += get_appform_info_skills(data, dc, 'customSkills', 'Навыки')

    # образование
    dc = {'education': ''}
    ret += get_appform_info_str(data, dc, 'Образование')

    # опыт работы
    dc = {'experience': ''}
    ret += get_appform_info_str(data, dc, 'Опыт работы')

    # пройденные в УИИ курсы
    dc = {'courseDataScience': 'Data Science', 'coursePython': 'Python разработчик'}
    ret += get_appform_info_str(data, dc, 'Курсы УИИ')

    return ret
