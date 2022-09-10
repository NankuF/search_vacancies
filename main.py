"""
Вариант скрипта для запуска через консоль.
"""
import argparse
import datetime
import os
import time
from collections import Counter
from typing import List

import openpyxl
from openpyxl.styles import Font, Border, Side, Alignment, NamedStyle

from hh_api import Headhunter


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vacancy', type=str, help='Название вакансии.')
    parser.add_argument('--location', type=str, help='Можно ввести город, регион или страну.')
    parser.add_argument('--need_salary', action='store_true',
                        help='Укажите этот ключ, если хотите увидеть вакансии с указанной зарплатой.')
    parser.add_argument('--period', type=int,
                        help='За какой период искать работу. Указать количество дней. Максимум 30.')
    parser.add_argument('--schedule', type=str,
                        help='График работы: '
                             'remote | fullDay | shift | flexible  - '
                             'удаленная работа; полный день; сменный график; гибкий график. '
                             'Этот ключ можно не указывать.')
    return parser


def sheet_style(sheet):
    """
    Настроить стили таблицы excel.
    """
    alignment = Alignment(horizontal='center', vertical='center')

    for columns in sheet:
        for column in columns:
            column.font = Font(size=9)

    # Let's create a style template for the header row
    header = NamedStyle(name='header')
    header.font = Font(bold=True)
    header.border = Border(bottom=Side(border_style='thin'))
    header.alignment = Alignment(horizontal='center', vertical='center')

    # Now let's apply this to all first row (header) cells
    header_row = sheet[1]
    for cell in header_row:
        cell.style = header
        cell.alignment = alignment


def get_vacancies(vacancy: str = None,
                  location: str = None,
                  period: str or int = None,
                  need_salary: bool = None,
                  schedule: str = None,
                  save_vacancies: bool = True) -> List[dict]:
    """
    Главная функция для управления получением вакансий. Предполагается, что запуск будет через консоль.
    :param vacancy: Название вакансии.
    :param location: Местоположение на русском языке.
    :param period: За какой период искать в днях.
    :param need_salary: Искать вакансии только с указанными зарплатами.
    :param schedule: График работы, если None, то все графики работы.
    :param save_vacancies: Сохранять вакансии в excel или нет.
    :return: список собранных вакансий.
    """
    parser = create_parser()
    args = parser.parse_args()
    vacancy_name = args.vacancy or vacancy or 'Программист Python'
    location = args.location or location or 'Москва'
    need_salary = args.need_salary or need_salary or False
    period = args.period or period or '1'
    schedule = args.schedule or schedule or None

    hh = Headhunter()

    vacancies = hh.get_hh_vacancies(vacancy=vacancy_name,
                                    location=location,
                                    only_with_salary=need_salary,
                                    period=period,
                                    schedule=schedule,
                                    )

    book = openpyxl.Workbook()
    sheet = book.active

    collected_vacancies = []
    for i, vacancy in enumerate(vacancies):
        temp = {}
        temp['id'] = vacancy['id']
        temp['published_at'] = vacancy['published_at'].strip('+0300')
        temp['area'] = vacancy['area']['name']
        temp['name'] = vacancy['name']
        temp['employer'] = vacancy['employer']['name']
        temp['salary_from'] = vacancy['salary']['from'] if vacancy['salary'] else ''
        temp['salary_to'] = vacancy['salary']['to'] if vacancy['salary'] else ''
        temp['currency'] = vacancy['salary']['currency'] if vacancy['salary'] else ''
        temp['gross'] = 'Да' if vacancy['salary'] and vacancy['salary']['gross'] else ''
        temp['experience'] = vacancy['experience'] if vacancy['experience'] else ''
        temp['schedule'] = vacancy['schedule']['name']
        temp['key_skills'] = vacancy.get('key_skills', '')
        temp['address'] = vacancy['address']['raw'] if vacancy['address'] else ''
        temp['station'] = vacancy['address']['metro']['station_name'] if vacancy['address'] is not None and \
                                                                         vacancy['address']['metro'] is not None else ''
        temp['url'] = vacancy['alternate_url']
        temp['has_test'] = vacancy['has_test']
        collected_vacancies.append(temp)
    fieldnames = ['id',
                  'published_at',
                  'area',
                  'name',
                  'employer',
                  'salary_from',
                  'salary_to',
                  'currency',
                  'gross',
                  'experience',
                  'schedule',
                  'address',
                  'station',
                  'url',
                  'has_test',
                  'key_skills', ]
    sheet.append(['Id',
                  'Дата публикации',
                  'Местоположение',
                  'Вакансия',
                  'Работодатель',
                  'Зп от',
                  'Зп до',
                  'Валюта',
                  'До вычета налога',
                  'Опыт',
                  'График работы',
                  'Адрес',
                  'Станция метро',
                  'Url',
                  'Тестовое задание',
                  'Навыки', ])
    for vacancy in collected_vacancies:
        values = (vacancy[k] for k in fieldnames)
        sheet.append(values)

    sheet_style(sheet)
    sheet.auto_filter.ref = sheet.dimensions

    if save_vacancies and collected_vacancies:
        os.makedirs('vacancies', exist_ok=True)
        timestamp = int(time.mktime(datetime.datetime.now().timetuple()))
        try:
            book.save(f'vacancies/{vacancy_name}_{timestamp}.xlsx')
            print('Вакансии сохранены в папку "vacancies".')
        except PermissionError:
            print('ОШИБКА! Закройте Excel и запустите скрипт заново.')
    else:
        print('Вакансий по такому запросу не найдено.')

    return collected_vacancies


def run_skills_counter(vacancy, location='Россия', period=30, save_skills=True) -> List[str]:
    """
    Запускает подсчет ключевых навыков и сохраняет их в txt.
    :param vacancy: Название вакансии.
    :param location: Местоположение на русском языке.
    :param period: За какой период искать в днях.
    :param save_skills: Сохранять ключевые навыки в txt или нет.
    :return: список собранных вакансий.
    """
    summary_skills = [vacancy.get('key_skills') for vacancy in get_vacancies(vacancy, location, period,
                                                                             save_vacancies=False)]
    sum_skills = []
    for lst in summary_skills:
        for skill in lst.split(', '):
            sum_skills.append(skill)
    skills_count = Counter(sum_skills)
    skills = list(map(lambda key: (key, skills_count[key]), skills_count))
    sorted_skills = sorted(skills, key=lambda x: x[1], reverse=True)
    skills = list(map(lambda skill: f'{skill[0]} = {skill[1]}', sorted_skills))

    if save_skills:
        os.makedirs('skills', exist_ok=True)
        with open('skills/skills.txt', 'w', encoding='utf-8') as f:
            for skill in skills:
                f.write(f"{skill}\n")

    return skills


def main():
    get_vacancies()


if __name__ == '__main__':
    main()
