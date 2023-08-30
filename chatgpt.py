# точка входа для генерации резюме с помощью chatGPT
from faker import Faker
from random import randint


# формирование резюме
def gpt_resume_builder(user_id: int):
    fake = Faker()
    fake_resume = fake.words(nb=randint(50, 100))
    return fake_resume
