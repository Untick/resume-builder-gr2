import uvicorn
from faker import Faker
from random import randint
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

import auth
import models
import crud
import pdf
import utils
import chatgpt

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
            result = chatgpt.gpt_resume_builder_entry_point(user_id)
            fake = Faker()
            fake_resume = fake.words(nb=randint(100, 500))
            crud.save_resume(user_id, ', '.join(fake_resume))

        if 'btnPDF' in data:
            pdf.get_pdf_resume(user_id)
            error = 'Функция выгрузки PDF ещё не реализована'

    # чтение данных из базы
    user_appform = crud.get_appform(user_id)
    user_resume = crud.get_resume(user_id)

    context = {'request': request, 'success': success, 'error': error, 
               'data': user_appform, 'resume': user_resume
               }
    return templates.TemplateResponse('resume.html', context=context)


# Выход из учётной записи
@app.get('/logout')
async def logout():
    # удаление токена из cookies и перенаправление на главную страницу
    response = RedirectResponse('/')
    response.delete_cookie(key='token')
    return response


if __name__ == "__main__":
    # первый запуск следует осуществлять в IDE, чтобы создать базу данных,
    # в дальнейшем можно запускать через терминал: uvicorn main:app --reload

    models.Base.metadata.create_all(models.engine)  # создание базы данных
    uvicorn.run(app)  # запуск сервера uvicorn