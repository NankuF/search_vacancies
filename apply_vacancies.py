import asyncio
import logging
import textwrap as tw
import time

import environs
from environs import Env
from telethon import TelegramClient

from hh_api import Headhunter

logger = logging.getLogger('app.apply_vacancies')


def check_secrets(*args):
    env = Env()
    env.read_env()
    is_all_true = False
    for arg in args:
        is_all_true = True if env(arg, None) else False
    return is_all_true


async def send_to_telegram_channel(message: str):
    telethon_api_id = env.int('TELETHON_API_ID')
    telethon_api_hash = env.str('TELETHON_API_HASH')
    private_channel_id = env.int('PRIVATE_CHANNEL_ID')

    client = TelegramClient('session_name', telethon_api_id, telethon_api_hash)
    await client.start()
    await client.send_message(entity=private_channel_id, message=message)


def message():
    github = 'https://github.com/NankuF/search_vacancies'
    email = 'poltoranin_valeriy@mail.ru'
    telegram = 'https://t.me/nankuF'
    linkedin = 'https://www.linkedin.com/in/vpoltoranin/'
    resume_url = 'https://spb.hh.ru/resume/eb3cd5ebff0b3410440039ed1f59646c424a5a'
    message = f"""\
    Добрый день! Пока вы читаете это сообщение - я пишу код.
    Меня зовут Валерий Полторанин и данный отклик отправлен автоматически, в рамках проекта автоматизации поиска вакансий.
    Я открыт к предложениям и нахожусь в поиске работы.

    Мое резюме: {resume_url}
    Код приложения вы можете увидеть на моем Github: {github}

    Мои контакты: 
    email: {email}
    telegram: {telegram}
    linkedin: {linkedin}
    С уважением, Валерий Полторанин.
    """
    message_without_indent = tw.dedent(message)

    return message_without_indent


def run_apply_vacancies(vacancies_amount: int, interval: int):
    """
    :param vacancies_amount: количество вакансий, на которые произойдет отклик.
    :param interval: интервал между откликами на вакансию, в секундах.

    """
    hh = Headhunter()
    resume_id = hh.get_resume_id(resume_name=hh.resume_name)

    while True:
        collected_vacancies = hh.get_hh_vacancies(vacancy='Python', location='Россия', period=1, only_with_salary=False)
        filtered_vacancies = hh.filter_vacancies(vacancies=collected_vacancies,
                                                 blacklist=['Преподаватель', 'Senior', 'Аналитик', 'Старший', 'QA',
                                                            'Team',
                                                            'Автор', 'Ведущий', 'тест', 'Data', 'Математик', 'С++',
                                                            'C++',
                                                            'Педагог'])
        if len(filtered_vacancies[:vacancies_amount]):
            # todo в api есть ограничение на кол-во откликов, но неизвестен этот предел.
            for vacancy in filtered_vacancies[:vacancies_amount]:
                msg = hh.apply_vacancy(resume_id=resume_id, vacancy=vacancy, message=message())
                if check_secrets('TELETHON_API_ID', 'TELETHON_API_HASH', 'PRIVATE_CHANNEL_ID'):
                    asyncio.run(send_to_telegram_channel(message=msg))
        time.sleep(interval)


if __name__ == '__main__':
    env = environs.Env()
    env.read_env()
    vacancies_amount = env.int('HH_VACANCIES_AMOUNT')
    interval = env.int('HH_INTERVAL')
    run_apply_vacancies(vacancies_amount=vacancies_amount, interval=interval)
