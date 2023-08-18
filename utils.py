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
