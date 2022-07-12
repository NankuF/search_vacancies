import string
import time
from typing import List

import openpyxl
import requests
from tqdm import tqdm


class Headhunter:
    HEADERS = {'User-Agent': '(fireloki87@gmail.com)'}

    def __init__(self):
        self.session = requests.Session()
        self.dictionaries = self.get_dictionaries()

    def get_hh_vacancies(self, vacancy: str, location: str, only_with_salary: bool, period: int, schedule: str = None,
                         ) -> List[dict]:
        """
        Ищет вакансии на Headhunter.

        FIXME
        has_test - тестирование при отправке резюме,
        snippet - краткие требования по вакансии. {'requirement': 'Отличное знание <highlighttext>Python</highlighttext>, Django, Celery, PostgreSQL, Redis, ClickHouse (желателен опыт работы от 3-х лет). Опыт написания unit-тестов. ',
                                                   'responsibility': 'Участие в разработке проектов в сфере блокчейн технологий. Разработка backend (REST API ) для сервисов, как в рамках новых проектов, так...'}
        url - ссылка на api вакансии c расширенной информацией.
        'alternate_url' - ссылка на вакансию на сайте hh.
        'experience': {'id': 'between1And3', 'name': 'От 1 года до 3 лет'}
        'employment': {'id': 'full', 'name': 'Полная занятость'}



        :param schedule: remote | fullDay | shift | flexible - удаленная работа; полный день; сменный график; гибкий график.
        :param period: за какое время искать вакансии. Максимум за 30 дней.
        :param only_with_salary: True|False, вакансии с указанной зарплатой.
        :param vacancy: название вакансии.
        :param location: город или регион.
        :return: список словарей со средней зарплатой.
        """

        base_url = 'https://api.hh.ru/'
        search_vacancies_url = f'{base_url}vacancies'

        start_timestamp = time.time()

        collected_vacancies = []
        payload = {'text': vacancy,
                   'area': self.get_location_id(name=location),
                   'period': period,
                   'professional_role': self.get_professional_role(name=vacancy),
                   'only_with_salary': only_with_salary,
                   'page': 0,
                   'search_field': {'name': 'в названии вакансии'},
                   'schedule': schedule,
                   'per_page': 100,
                   }

        while True:
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

        :return: словари используемые в API Headhunter.
        """
        url = 'https://api.hh.ru/dictionaries'
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def predict_rub_salary_hh(self, vacancy: dict) -> int:

        """
        Рассчитывает среднюю зарплату в рублях для одной вакансии.

        :param vacancy: словарь с данными о вакансии.
        :return: усредненная зарплата в рублях.
        """

        if vacancy['currency'] not in 'RUR':
            currencies = self.dictionaries['currency']
            for currency in currencies:
                if vacancy['currency'] == currency['code']:
                    if vacancy['from']:
                        vacancy['from'] //= currency['rate']
                    if vacancy['to']:
                        vacancy['to'] //= currency['rate']
        if vacancy['from'] and vacancy['to']:
            return (vacancy['from'] + vacancy['to']) / 2
        if vacancy['from']:
            return vacancy['from'] * 1.2
        if vacancy['to']:
            return vacancy['to'] * 0.8

    def get_average_salary(self, collected_vacancies: list) -> dict:
        """
        Рассчитывает среднюю зарплату в рублях для списка вакансий.

        :param collected_vacancies: список вакансий.
        :return: словарь с рассчитанной средней зарплатой в рублях.
        """
        if collected_vacancies:
            vacancies_with_salary = [self.predict_rub_salary_hh(vacancy['salary']) for vacancy in
                                     collected_vacancies if vacancy['salary']]
            average_salary = sum(vacancies_with_salary) / len(vacancies_with_salary)

        return {
            'vacancies_found': len(collected_vacancies),
            'vacancies_with_salary': len(vacancies_with_salary) if collected_vacancies else 0,
            'average_salary': f'{int(average_salary)} RUR' if collected_vacancies else 0,
        }


def main():
    hh = Headhunter()
    vacancies = hh.get_hh_vacancies(vacancy='Программист Python',
                                    location='Санкт-Петербург',
                                    only_with_salary=False,
                                    period=1,
                                    # schedule='fullDay',
                                    )

    excel_structure = ['id',
                       'published_at',
                       'area',
                       'name',
                       'employer',
                       'average salary RUR',
                       'experience',
                       'schedule',
                       'key_skills',
                       'address',
                       'station',
                       'url',
                       'has_test']
    alphabet = list(string.ascii_uppercase)

    book = openpyxl.Workbook()
    sheet = book.active
    for i, el in enumerate(excel_structure):
        sheet[f'{alphabet[i]}1'] = excel_structure[i].upper()

    row = 2
    for i, vacancy in enumerate(vacancies):
        clear_vacancies = []
        id = vacancy['id']
        published_at = vacancy['published_at'].strip('+0300')
        area = vacancy['area']['name']
        name = vacancy['name']
        employer = vacancy['employer']['name']
        salary = f'{int(hh.predict_rub_salary_hh(vacancy["salary"]))}' if vacancy['salary'] else ''
        experience = vacancy['experience'] if vacancy['experience'] else ''
        schedule = vacancy['schedule']['name']
        key_skills = vacancy.get('key_skills', '')
        address = vacancy['address']['raw'] if vacancy['address'] else ''
        station = vacancy['address']['metro']['station_name'] if vacancy['address'] is not None and vacancy['address'][
            'metro'] is not None else ''
        url = vacancy['alternate_url']
        has_test = vacancy['has_test']
        clear_vacancies.extend((id,
                                published_at,
                                area,
                                name,
                                employer,
                                salary,
                                experience,
                                schedule,
                                key_skills,
                                address,
                                station,
                                url,
                                has_test))
        del (id,
             area,
             name,
             employer,
             salary,
             experience,
             schedule,
             key_skills,
             address,
             station,
             url,
             has_test,
             published_at,
             vacancy,)

        for n, vac in enumerate(clear_vacancies):
            sheet[row][n].value = vac

        row += 1

    book.save('mybook.xlsx')


if __name__ == '__main__':
    main()
