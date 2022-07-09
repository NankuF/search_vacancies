import collections

import terminaltables

from headhunter import get_hh_vacancies
from superjob import get_superjob_vacancies


def main():
    """
    Отображает результаты расчета средней зарплаты по языкам программирования в табличном виде в терминале.
    Т.к superjob не поддерживает выдачу вакансий по регионам, следует указывать только город.
    """
    popular_languages = [
        'JavaScript',
        'Java',
        'Python',
        'Ruby',
        'PHP',
        'C++',
        'C#',
        'C',
        'Go',
    ]

    SearchFunction = collections.namedtuple('SearchFunction', ['func', 'name'])
    headhunter = SearchFunction(func=get_hh_vacancies, name='Headhunter')
    superjob = SearchFunction(func=get_superjob_vacancies, name='Superjob')

    funcs = [headhunter, superjob]

    language_salaries = {}
    for func in funcs:
        for language in popular_languages:
            language_salaries[language] = func.func(vacancy=f'Программист {language}', location='Москва')

        table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
        _ = []
        for lang_data in language_salaries.items():
            _.append([lang_data][0][0])
            _.extend(lang_data[1].values())
            table_data.append(_)
            _ = []
        table = terminaltables.SingleTable(table_data, func.name)

        print(table.table)


if __name__ == '__main__':
    main()
