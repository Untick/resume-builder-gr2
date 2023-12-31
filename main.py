import threading

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse


import auth
import models
import crud
import pdf
import utils
import chatgpt

import telegram

# создаём приложение fastapi
app = FastAPI(title='Resume builder')

# монтируем директорию со статичными файлами
app.mount('/static', StaticFiles(directory='static'), name='static')

# подключаем библиотеку шаблонов jinja2 к директории templates
templates = Jinja2Templates(directory='templates')


@app.get('/')
async def index(request: Request):
    # проверка авторизации, получение имени пользователя
    _, username = utils.get_user_auth(request)

    context = {'request': request, 'username': username}
    return templates.TemplateResponse('index.html', context=context)


@app.post('/')
async def index_post(request: Request):
    # получение логина и пароля из формы
    data = await request.form()
    login = data['login'] if 'login' in data else ''
    password = data['password'] if 'password' in data else ''

    # если логин и/или пароль не введены, ошибка
    if not login or not password:
        return templates.TemplateResponse('index.html',
                                          {'request': request,
                                           'error': 'Введите корректный логин и пароль'})

    # проверка пользователя
    user = crud.get_user_by_name(login)
    if user:
        # пользователь существует, проверка пароля
        if auth.pwd_context.verify(password, user[2]):
            # пароль верный, делаем перенаправление на страницу составления резюме
            response = utils.get_redirect('/resume', {'id': user[0], 'user': user[1]})
            return response
        else:
            error = 'Неверный пароль'
    else:
        # пользователя нет в базе, добавляем
        hashed_password = auth.pwd_context.hash(password)
        user_id = crud.create_user(login, hashed_password)

        if user_id:
            # пользователь добавлен успешно, перенаправление на страницу с резюме
            response = utils.get_redirect('/resume', {'id': user_id, 'user': login})
            return response
        else:
            error = 'Ошибка добавления пользователя'

    return templates.TemplateResponse('index.html', {'request': request, 'error': error})


@app.route('/resume', methods=['GET', 'POST'])
async def resume_appform(request: Request):
    # проверка авторизации, получение id пользователя
    user_id, username = utils.get_user_auth(request)
    if not user_id:
        # пользователь неавторизован, возвращаемся на главную страницу
        return RedirectResponse('/')

    success = None
    error = None

    if request.method == 'POST':
        # получение данных из формы
        data = await request.form()

        # сохранение данных в базу
        if 'btnSave' in data:
            if crud.save_appform(user_id, dict(data)):
                success = 'Данные сохранены'
            else:
                error = 'Ошибка сохранения данных'

        # формирование и сохранение резюме
        if 'btnGen' in data:
            result = chatgpt.gpt_resume_builder(user_id)
            if result:
                if not crud.save_resume(user_id, ', '.join(result)):
                    error = 'Ошибка сохранения резюме'
            else:
                error = 'Ошибка генерации резюме'

        if 'btnPDF' in data:
            pdf.get_pdf_resume(user_id)
            error = 'Функция выгрузки PDF ещё не реализована'

    # чтение данных из базы
    user_appform = crud.get_appform(user_id)
    user_resume = crud.get_resume(user_id)

    context = {'request': request, 'success': success, 'error': error, 'data': user_appform, 'resume': user_resume}
    return templates.TemplateResponse('resume.html', context=context)


class TgApi(BaseModel):
    username: str | None = None
    token: str | None = None


# API для обработчика команды /form во внешнем тг-боте
@app.post('/tgbot/form')
async def tgbot_form(data: TgApi):
    if not utils.check_tg_api_data(data):
        return
    return {'message', await utils.form_command(data.username)}


# API для обработчика команды /resume во внешнем тг-боте
@app.post('/tgbot/resume')
async def tgbot_resume(data: TgApi):
    if not utils.check_tg_api_data(data):
        return
    return {'message', await utils.resume_command(data.username)}


# API для обработчика команды /generate во внешнем тг-боте
@app.post('/tgbot/generate')
async def tgbot_resume(data: TgApi):
    if not utils.check_tg_api_data(data):
        return
    return {'message', await utils.generate_command(data.username)}


# Выход из учётной записи
@app.get('/logout')
async def logout():
    # удаление токена из cookies и перенаправление на главную страницу
    response = RedirectResponse('/')
    response.delete_cookie(key='token')
    return response


# для подключения telegram-бота к приложению раскомментировать код ниже

@app.on_event('startup')
async def on_startup():
    # запускаем пулинг в отдельном потоке, чтобы не блокировать работу FastAPI
    my_thread = threading.Thread(target=telegram.bot.infinity_polling)
    my_thread.start()


@app.on_event('shutdown')
async def on_shutdown():
    telegram.bot.stop_bot()


if __name__ == "__main__":
    # первый запуск следует осуществлять в IDE, чтобы создать базу данных,
    # в дальнейшем можно запускать через терминал: uvicorn main:app --reload

    models.Base.metadata.create_all(models.engine)  # создание базы данных
    uvicorn.run(app)  # запуск сервера uvicorn
    # uvicorn.run(app, host='0.0.0.0', port=8000)  # для доступа по локальной сети
