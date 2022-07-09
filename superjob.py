from pprint import pprint

import environs
import requests

from headhunter import get_dictionaries


def predict_rub_salary_superjob(vacancy: dict) -> int:
    """
    Рассчитывает зарплату в рублях.

    :param vacancy: словарь с данными о вакансии.
    :return: зарплата в рублях.
    """
    if vacancy['currency'] not in 'RUR':
        currencies = get_dictionaries()['currency']
        for currency in currencies:
            if vacancy['currency'] == currency['code']:
                if vacancy['payment_from']:
                    vacancy['payment_from'] //= currency['rate']
                if vacancy['payment_to']:
                    vacancy['payment_to'] //= currency['rate']
    if vacancy['payment_from'] and vacancy['payment_to']:
        return (vacancy['payment_from'] + vacancy['payment_to']) / 2
    if vacancy['payment_from']:
        return vacancy['payment_from'] * 1.2
    if vacancy['payment_to']:
        return vacancy['payment_to'] * 0.8


def get_superjob_vacancies(vacancy: str, location: str) -> dict:
    """
    Ищет вакансии на Superjob.

    :param vacancy: название вакансии.
    :param location: город или регион.
    :return: словарь со средней зарплатой.
    """
    env = environs.Env()
    env.read_env()
    secret_key = env.str('SUPERJOB_SECRET_KEY')

    headers = {'X-Api-App-Id': secret_key}

    payload = {'town': location,
               'keywords[0][srws]': 1,
               'keywords[0][skwc]': 'and',
               'keywords[0][keys]': vacancy,
               'no_agreement': 1,
               'period': 30,
               'count': 100,
               'page': 0,
               }

    base_url = 'https://api.superjob.ru/2.0/'
    search_vacancies_url = f'{base_url}vacancies'

    collected_vacancies = []
    vacancies_count = 0
    cycle = True
    while cycle:
        resp = requests.get(search_vacancies_url, headers=headers, params=payload)
        resp.raise_for_status()

        cycle = resp.json()['more']
        vacancies_count = resp.json()['total']
        collected_vacancies.extend(resp.json()['objects'])
        payload['page'] += 1

    average_salary = 0
    if collected_vacancies:
        average_salary = sum([predict_rub_salary_superjob(vacancy) for vacancy in collected_vacancies]) / len(
            collected_vacancies)

    return {
        'vacancies_found': vacancies_count,
        'vacancies_processed': len(collected_vacancies),
        'average_salary': int(average_salary),
    }


if __name__ == '__main__':
    pprint(get_superjob_vacancies('Программист Javasript', 'Москва'))
