from pprint import pprint

import requests

HEADERS = {'User-Agent': '(fireloki87@gmail.com)'}


def get_location_id(name: str) -> str:
    """
    Получает название региона или города.
    Пример №1: Красноярский край
    Пример №2: Новосибирск

    :param name: название региона или города.
    :return: id региона или города.
    """

    url = 'https://api.hh.ru/areas'
    resp = requests.get(url, headers=HEADERS)

    for country in resp.json():
        for region in country['areas']:
            if region['name'].lower() == name.lower():
                return region['id']
            else:
                for city in region['areas']:
                    if name.lower() == city['name'].lower():
                        return city['id']
    raise NameError(f'{get_location_id.__name__}: Город не найден.')


def get_professional_role(name: str) -> str:
    """
    Получает строку идентификаторов специализации.

    :param name: название специализации.
    :return: строка идентификаторов специализации.
    """
    url = 'https://api.hh.ru/professional_roles'

    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    professional_roles = resp.json()
    ids = []
    for category in professional_roles['categories']:
        for role in category['roles']:
            if name.lower() in role['name'].lower():
                ids.append(role['id'])
    return ','.join(set(ids))


def get_dictionaries() -> dict:
    """
    Получает словари используемые в API Headhunter.

    :return: словари используемые в API Headhunter.
    """
    url = 'https://api.hh.ru/dictionaries'
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def predict_rub_salary_hh(vacancy: dict) -> int:
    """
    Рассчитывает зарплату в рублях.

    :param vacancy: словарь с данными о вакансии.
    :return: зарплата в рублях.
    """
    if vacancy['currency'] not in 'RUR':
        currencies = get_dictionaries()['currency']
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


def get_hh_vacancies(vacancy: str, location: str) -> dict:
    """
    Ищет вакансии на Headhunter.

    :param vacancy: название вакансии.
    :param location: город или регион.
    :return: словарь со средней зарплатой.
    """
    payload = {'text': vacancy,
               'area': get_location_id(name=location),
               'period': 30,
               'professional_role': get_professional_role('программист'),
               'only_with_salary': True,
               'page': 0,
               'search_field': {'name': 'в названии вакансии'},
               }

    base_url = 'https://api.hh.ru/'
    search_vacancies_url = f'{base_url}vacancies'

    resp = requests.get(search_vacancies_url, headers=HEADERS, params=payload)
    resp.raise_for_status()
    vacancies = resp.json()
    collected_vacancies = vacancies['items']

    while vacancies['page'] < vacancies['pages'] - 1:
        payload['page'] += 1
        resp = requests.get(search_vacancies_url, headers=HEADERS, params=payload)
        resp.raise_for_status()
        vacancies = resp.json()
        collected_vacancies.extend(vacancies['items'])

    average_salary = 0
    if collected_vacancies:
        average_salary = sum([predict_rub_salary_hh(vacancy['salary']) for vacancy in collected_vacancies]) / len(
            collected_vacancies)

    return {
        'vacancies_found': vacancies['found'],
        'vacancies_processed': len(collected_vacancies),
        'average_salary': int(average_salary),
    }


if __name__ == '__main__':
    pprint(get_hh_vacancies('Программист Javasript', 'Москва'))
