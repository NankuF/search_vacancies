import logging
import time
import webbrowser
from typing import List

import environs
import requests
from tqdm import tqdm


def init_logger(name):
    logger = logging.getLogger(name)
    FORMAT = '%(asctime)s - %(name)s:%(lineno)s - %(levelname)s - %(message)s'
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(FORMAT))
    sh.setLevel(logging.DEBUG)
    fh = logging.FileHandler(filename='logs/logs.log')
    fh.setFormatter(logging.Formatter(FORMAT))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.debug('logger was initialized')


init_logger('app')
logger = logging.getLogger('app.hh_api')


class Headhunter:

    def __init__(self):
        self.session = requests.Session()
        self.dictionaries = self.get_dictionaries()

        self.env = environs.Env()
        self.env.read_env()
        self.resume_name = self.env.str('HH_RESUME_NAME')
        self.developer_email = self.env.str('DEVELOPER_EMAIL', 'this_user_not_developer@fakemail.com')
        self.client_id = self.env.str('HH_CLIENT_ID', None)
        self.client_secret = self.env.str('HH_CLIENT_SECRET', None)
        if not all([self.client_id, self.client_secret]):
            msg = """Создайте приложение по адресу https://dev.hh.ru/admin, затем сохраните CLIENT_ID и CLIENT_SECRET в .env """
            logging.critical(msg)
            raise ValueError(msg)

        self.app_access_token = self.env.str('HH_APP_ACCESS_TOKEN', None)
        if not self.app_access_token:
            self.__app_authorization()
        self.user_access_token = self.env.str('HH_USER_ACCESS_TOKEN', None)
        self.user_refresh_token = self.env.str('HH_USER_REFRESH_TOKEN', None)
        if not all([self.user_access_token, self.user_refresh_token]):
            self.__check_user_authorization()
        self.user_authorization_headers = {'Authorization': f'Bearer {self.user_access_token}'}
        self.headers = {'User-Agent': self.developer_email}

        logger.debug('Инициализация приложения: ОК')

    def __app_authorization(self):
        """
        Получение токена приложения (авторизация приложения).
        Токен имеет неограниченный срок жизни, интервал запроса - раз в 5 мин.
        """
        if not self.app_access_token:
            response = self.session.post('https://hh.ru/oauth/token',
                                         data={'grant_type': 'client_credentials',
                                               'client_id': self.client_id,
                                               'client_secret': self.client_secret},
                                         headers={'Content-Type': 'application/x-www-form-urlencoded'})
            response.raise_for_status()
            app_authorization_info = response.json()
            if 'access_token' in app_authorization_info:
                self.app_access_token = app_authorization_info['access_token']
                with open('.env', 'a') as file:
                    file.write(f'\nAPP_ACCESS_TOKEN={self.app_access_token}')
            else:
                msg = 'Не удалось получить токен приложения. Повторите через 5 минут.'
                logger.critical(msg)
                raise ValueError(msg)
        else:
            logger.debug('Авторизация приложения: ОК')

    def __check_user_authorization(self):
        if not self.user_access_token:
            self.__user_authorization()
        else:
            response_info = self.get_user_info()
            if response_info.get('errors'):
                self.__user_authorization()
            else:
                logger.debug('Авторизация пользователя: ОК')

    def __user_authorization(self):
        if self.app_access_token:
            # todo срок жизни токена пользователя - 14 дней. В течении этого срока можно держать скрипт на сервере
            # todo затем потребуется обновить этот токен.
            is_true = webbrowser.open(f'https://hh.ru/oauth/authorize?response_type=code&'
                                      f'client_id={self.client_id}', new=2, autoraise=True)
            if is_true:
                authorization_code = input('Нажмите "Продолжить" и введите код авторизации из url, параметр code= : ')
        else:
            msg = 'Необходимо получить токен авторизации приложения.'
            logger.critical(msg)
            raise ValueError(msg)

        # Получение access и refresh токенов
        response = self.session.post('https://hh.ru/oauth/token', data={
            'grant_type': 'authorization_code',
            'client_id': {self.client_id},
            'client_secret': {self.client_secret},
            'code': {authorization_code}})
        response.raise_for_status()
        user_tokens_info = response.json()
        self.user_access_token = user_tokens_info['access_token']
        self.user_refresh_token = user_tokens_info['refresh_token']
        with open('.env', 'a') as file:
            file.write(f'\nUSER_ACCESS_TOKEN={self.user_access_token}')
            file.write(f'\nUSER_REFRESH_TOKEN={self.user_refresh_token}')

    def get_user_info(self):
        response = self.session.get('https://api.hh.ru/me', headers={**self.user_authorization_headers, **self.headers})
        response.raise_for_status()
        return response.json()

    def get_resume_id(self, resume_name: str):
        response = self.session.get('https://api.hh.ru/resumes/mine', headers=self.user_authorization_headers)
        response.raise_for_status()
        resumes = response.json()
        for resume in resumes['items']:
            if resume['title'] == resume_name:
                return resume['id']
            else:
                msg = 'Резюме с таким названием не найдено.'
                logger.critical(msg)
                raise NameError(msg)

    def filter_vacancies(self, vacancies: list, blacklist: list):
        """
        Фильтрация вакансий по следующим условиям:
        1. Проверка на стаж и требование пройти тест.
        2. Проверка на вхождение слов из названия вакансии в blacklist.
        3. Проверка - откликался ли уже на эту вакансию.
        """
        no_experience = 'Нет опыта'
        between_1_and_3 = 'От 1 года до 3 лет'
        between_3_and_6 = 'От 3 до 6 лет'
        more_6 = 'Более 6 лет'

        filtered_on_apply_vacancies = []
        for vacancy in vacancies:
            if vacancy['experience'] in [between_3_and_6, more_6] or vacancy['has_test']:
                continue
            elif blacklist:
                has_stop_word = False
                for word in blacklist:
                    if word.lower() in vacancy['name'].lower():
                        has_stop_word = True
                        break
                if not has_stop_word:
                    response = self.session.get(f'https://api.hh.ru/vacancies/{vacancy["id"]}/resumes_by_status',
                                                headers=self.user_authorization_headers)
                    response.raise_for_status()
                    response_info = response.json()
                    if not response_info['already_applied']:
                        filtered_on_apply_vacancies.append(vacancy)
                    else:
                        logger.debug(f'Ранее откликались на: {vacancy["name"]}, {vacancy["alternate_url"]}')

        return filtered_on_apply_vacancies

    def apply_vacancy(self, resume_id: str, vacancy: dict, message: str):

        params = {'resume_id': resume_id, 'vacancy_id': vacancy['id'], 'message': message}
        response = self.session.post('https://api.hh.ru/negotiations',
                                     headers={**self.user_authorization_headers, 'Content-Type': 'multipart/form-data'},
                                     params=params)
        if response.status_code == 201:
            logger.info(f'Отклик на вакансию "{vacancy["name"]}:{vacancy["employer"]["name"]}" - успешно отправлен.')

    def get_hh_vacancies(self, vacancy: str, location: str, only_with_salary: bool, period: int, schedule: str = None,
                         ) -> List[dict]:
        """
        Ищет вакансии на Headhunter.

        :param vacancy: название вакансии.
        :param location: город или регион.
        :param only_with_salary: True|False, вакансии с указанной зарплатой.
        :param period: за какое время искать вакансии. Максимум за 30 дней.
        :param schedule: remote | fullDay | shift | flexible - удаленная работа; полный день; сменный график; гибкий график.
        :return: список словарей со средней зарплатой.
        """

        base_url = 'https://api.hh.ru/'
        search_vacancies_url = f'{base_url}vacancies'

        start_timestamp = time.time()

        collected_vacancies = []
        payload = {'text': vacancy,
                   'area': self.get_location_id(name=location),
                   'period': period,
                   'only_with_salary': only_with_salary,
                   'page': 0,
                   'search_field': {'name': 'в названии вакансии'},
                   'schedule': schedule,
                   'per_page': 100,
                   # Дополнительный фильтр для поиска вакансий по специализации.
                   # Не отловлены ошибки, когда названия вакансии нет в словаре специализации, поэтому отключен.
                   # 'professional_role': self.get_professional_role(name=vacancy),
                   }

        while True:
            if len(collected_vacancies) == 2000:
                logger.warning('Достигнут предел выдачи в 2000 вакансий.')
                break

            resp = self.session.get(search_vacancies_url, params=payload, headers=self.user_authorization_headers)
            resp.raise_for_status()
            vacancies = resp.json()

            if vacancies['page'] >= vacancies['pages']:
                break

            for vacancy in tqdm(vacancies['items'], desc='Fetching data...', colour='GREEN'):
                resp = self.session.get(url=f'{search_vacancies_url}/{vacancy["id"]}',
                                        headers=self.user_authorization_headers)
                if resp.status_code != 200:  # todo 403 - капча. обработать.
                    return collected_vacancies
                key_skills = resp.json().get('key_skills', '')
                vacancy['key_skills'] = ', '.join([skill for skills in key_skills for skill in skills.values()])
                vacancy['experience'] = resp.json()['experience']['name']
                collected_vacancies.append(vacancy)
            payload['page'] += 1

        task_time = round(time.time() - start_timestamp, 2)
        rps = round(vacancies['found'] / task_time, 1)
        print(
            f"| Requests: {vacancies['found']}; Total time: {task_time} s; RPS: {rps} |\n"
        )
        logger.info(f"| Requests: {vacancies['found']}; Total time: {task_time} s; RPS: {rps} |\n")

        return collected_vacancies

    def get_location_id(self, name: str) -> str:

        """
        Получает id страны, региона или города.
        Пример №1: Россия
        Пример №2: Красноярский край
        Пример №3: Новосибирск

        :param name: название страны, региона или города.
        :return: id страны, региона или города.
        """

        url = 'https://api.hh.ru/areas'
        resp = self.session.get(url)

        for country in resp.json():
            if country['name'].lower() == name.lower():
                return country['id']
            for region in country['areas']:
                if region['name'].lower() == name.lower():
                    return region['id']
                else:
                    for city in region['areas']:
                        if name.lower() == city['name'].lower():
                            return city['id']

        msg = f'{self.get_location_id.__name__}: Город не найден.'
        logging.critical(msg)
        raise NameError(msg)

    def get_professional_role(self, name: str) -> str:

        """
        Получает строку идентификаторов специализации.

        :param name: название специализации.
        :return: строка идентификаторов специализации.
        """
        url = 'https://api.hh.ru/professional_roles'
        resp = self.session.get(url)
        resp.raise_for_status()
        professional_roles = resp.json()
        ids = []

        for category in professional_roles['categories']:
            for role in category['roles']:
                clear_role = [name.strip(',').strip() for name in role['name'].lower().split()]
                for role_name in clear_role:
                    if role_name in name.lower().split():
                        ids.append(role['id'])
        roles = ','.join(set(ids))
        return roles if roles != '' else None

    def get_dictionaries(self) -> dict:

        """
        Получает словари используемые в API Headhunter.
        Можно использовать для конвертации валют. Курс валют hh хранит в этом словаре.

        :return: словари используемые в API Headhunter.
        """
        url = 'https://api.hh.ru/dictionaries'
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()


if __name__ == '__main__':
    hh = Headhunter()
    info = hh.get_user_info()
    # Введите название резюме, которым хотите откликаться на вакансии.
    resume_id = hh.get_resume_id(resume_name='Junior+ Python developer')
    # Поиск вакансии по ключевому слову
    collected_vacancies = hh.get_hh_vacancies(vacancy='Python', location='Россия', period=3, only_with_salary=False)
    # Фильтрация полученных вакансий
    filtered_vacancies = hh.filter_vacancies(vacancies=collected_vacancies,
                                             blacklist=['Преподаватель', 'Senior', 'Аналитик', 'Старший', 'QA', 'Team',
                                                        'Автор', 'Ведущий', 'тест', 'Data', 'Математик', 'С++', 'C++',
                                                        'Педагог'])
