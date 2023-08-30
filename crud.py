from sqlalchemy import or_

from models import SessionLocal, User, AppForm, Resume


# Получение данных пользователя по имени
def get_user_by_name(username: str):
    with SessionLocal() as session:
        user = session.query(User).filter_by(username=username).first()

    if not user:
        return None

    return user.id, user.username, user.password


# Получение данных пользователя по telegram id
def get_user_by_tg_id(tg_id: str):
    if not tg_id:
        return None

    # обработка случая различных вариантов записи id telegram
    if tg_id.startswith('@'):
        tg_id2 = tg_id[1:]
    else:
        tg_id2 = f'@{tg_id}'

    with SessionLocal() as session:
        user_info = session.query(User.id, AppForm.name, AppForm.telegram) \
            .join(User, User.id == AppForm.id) \
            .filter(or_(AppForm.telegram == tg_id, AppForm.telegram == tg_id2)) \
            .first()

    if not user_info:
        return None

    return user_info.id, user_info.name


# Создание пользователя
def create_user(username: str, password: str):
    user_id = None

    # создание нового пользователя
    # with Session(engine) as session:
    with SessionLocal() as session:
        user = User(username=username, password=password)
        session.add(user)
        try:
            session.commit()
            user_id = user.id
        except Exception as ex:
            print(ex)
            session.rollback()
        finally:
            session.flush()
            session.close()

    return user_id


# Сохранение анкеты пользователя в базу
def save_appform(user_id: int, data: dict):
    # фильтруем словарь data с помощью списка из допустимых ключей

    # для данных типа bool
    keys_bool = ['skillPython', 'skillNumPy', 'skillPandas', 'skillMatplotlib', 'skillSeaborn',
                 'skillKeras', 'skillPytorch', 'skillTensorflow', 'skillNLP', 'skillGPT',
                 'skillObjectDetection', 'courseDataScience', 'coursePython']
    data_bool = {key: bool(value) for key, value in data.items() if key in keys_bool}
    data_bool.update({key: False for key in keys_bool if key not in data})

    # для данных типа str
    keys_str = ['name', 'birthdate', 'city', 'phone', 'email', 'telegram',
                'customSkills', 'education', 'experience']
    data_str = {key: str(value) for key, value in data.items() if key in keys_str}
    data_str.update({key: '' for key in keys_str if key not in data})

    try:
        with SessionLocal() as session:
            appform = session.query(AppForm).filter_by(id=user_id).first()

            if appform:
                # обновляем анкету существующего пользователя
                merged_dict = {**data_bool, **data_str}  # объединение словарей
                appform = session.query(AppForm).get(user_id)
                for key, value in merged_dict.items():
                    setattr(appform, key, value)
                session.commit()
            else:
                # создаем новую анкету пользователя
                merged_dict = {'id': user_id, **data_bool, **data_str}
                appform = AppForm(**merged_dict)
                session.add(appform)
                session.commit()
        return True
    except Exception as ex:
        print(ex)
        return False


# сохранение сгенерированного резюме в базу
def save_resume(user_id: int, resume: str):
    try:
        with SessionLocal() as session:
            user_resume = session.query(Resume).filter_by(id=user_id).first()
            if user_resume:
                setattr(user_resume, 'resume', resume)
                session.commit()
            else:
                user_resume = Resume(id=user_id, resume=resume)
                session.add(user_resume)
                session.commit()
        return True
    except:
        return False


# чтение анкеты пользователя из базы
def get_appform(user_id):
    try:
        with SessionLocal() as session:
            appform = session.query(AppForm).filter_by(id=user_id).first()
            return vars(appform)
    except:
        return None


# чтение резюме пользователя из базы
def get_resume(user_id):
    try:
        with SessionLocal() as session:
            user_resume = session.query(Resume).filter_by(id=user_id).first()
            return user_resume.resume
    except:
        return None
