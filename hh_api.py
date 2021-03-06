import sys
import time
from typing import List

import requests
from tqdm import tqdm


class Headhunter:
    HEADERS = {'User-Agent': '(my@gmail.com)'}

    def __init__(self):
        self.session = requests.Session()
        self.dictionaries = self.get_dictionaries()

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
