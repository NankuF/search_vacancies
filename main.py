import argparse
import csv
import datetime
import os
import time
from pprint import pprint

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


def main():
    parser = create_parser()
    args = parser.parse_args()
    vacancy_name = args.vacancy or 'Программист Python'
    location = args.location or 'Москва'
    need_salary = args.need_salary or False
    period = args.period or '1'
    schedule = args.schedule or None

    hh = Headhunter()

    vacancies = hh.get_hh_vacancies(vacancy=vacancy_name,
                                    location=location,
                                    only_with_salary=need_salary,
                                    period=period,
                                    schedule=schedule,
                                    )

    book = openpyxl.Workbook()
    sheet = book.active

    summary_skills = []
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
        summary_skills.append(temp['key_skills'])
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

    os.makedirs('vacancies', exist_ok=True)
    timestamp = int(time.mktime(datetime.datetime.now().timetuple()))

    sum_skills = []
    for lst in summary_skills:
        for skill in lst.split(', '):
            sum_skills.append(skill)
    from collections import Counter
    skills_count = Counter(sum_skills)
    pprint(skills_count)
    with open('skills.csv', 'w') as f:
        for key in skills_count.keys():
            f.write(f"{key},{skills_count[key]}\n")

    try:
        book.save(f'vacancies/{vacancy_name}_{timestamp}.xlsx')
    except PermissionError:
        print('ОШИБКА! Закройте Excel и запустите скрипт заново.')


# todo сделать exe и tkinter

if __name__ == '__main__':
    main()
