import sys
import time
import webbrowser
from typing import List

import environs
import requests
from tqdm import tqdm


class Headhunter:

    def __init__(self):
        self.env = environs.Env()
        self.env.read_env()
        self.developer_email = self.env.str('DEVELOPER_EMAIL', 'this_user_not_developer@fakemail.com')
        self.client_id = self.env.str('CLIENT_ID', None)
        self.client_secret = self.env.str('CLIENT_SECRET', None)
        if not all([self.client_id, self.client_secret]):
            raise ValueError(
                """Создайте приложение по адресу https://dev.hh.ru/admin,
                 затем сохраните CLIENT_ID и CLIENT_SECRET в .env """)

        self.app_access_token = self.env.str('APP_ACCESS_TOKEN', None)
        if not self.app_access_token:
            self.__app_authorization()
        self.user_access_token = self.env.str('USER_ACCESS_TOKEN', None)
        self.user_refresh_token = self.env.str('USER_REFRESH_TOKEN', None)
        if not all([self.user_access_token, self.user_refresh_token]):
            self.__check_user_authorization()
        self.user_authorization_headers = {'Authorization': f'Bearer {self.user_access_token}'}
        self.headers = {'User-Agent': self.developer_email}

        self.session = requests.Session()
        self.dictionaries = self.get_dictionaries()

        print('Инициализация приложения: ОК')

    def __app_authorization(self):
        """
        Получение токена приложения (авторизация приложения).
        Токен имеет неограниченный срок жизни, интервал запроса - раз в 5 мин.
        """
        if not self.app_access_token:
            response = requests.post('https://hh.ru/oauth/token',
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
                raise ValueError('Не удалось получить токен приложения. Повторите через 5 минут.')
        else:
            print('Авторизация приложения: ОК')

    def __check_user_authorization(self):
        if not self.user_access_token:
            self.__user_authorization()
        else:
            response_info = self.get_user_info()
            if response_info.get('errors'):
                self.__user_authorization()
            else:
                print('Авторизация пользователя: ОК')

    def __user_authorization(self):
        if self.app_access_token:
            is_true = webbrowser.open(f'https://hh.ru/oauth/authorize?response_type=code&'
                                      f'client_id={self.client_id}', new=2, autoraise=True)
            if is_true:
                authorization_code = input('Нажмите "Продолжить" и введите код авторизации из url, параметр code= : ')
        else:
            raise ValueError('Необходимо получить токен авторизации приложения.')

        # Получение access и refresh токенов
        response = requests.post('https://hh.ru/oauth/token', data={
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
                print('Достигнут предел выдачи в 2000 вакансий.', file=sys.stderr)
                break

            resp = self.session.get(search_vacancies_url, params=payload)
            resp.raise_for_status()
            vacancies = resp.json()

            if vacancies['page'] >= vacancies['pages']:
                break

            for vacancy in tqdm(vacancies['items'], desc='Fetching data...', colour='GREEN'):
                resp = self.session.get(url=f'{search_vacancies_url}/{vacancy["id"]}')
                resp.raise_for_status()
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
        raise NameError(f'{self.get_location_id.__name__}: Город не найден.')

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