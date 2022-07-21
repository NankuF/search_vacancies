"""
Вариант скрипта для компиляции в .exe
Использование на свой страх и риск, на ошибки и баги не проверялось.
"""
import time

from main import get_vacancies


def main():
    print('Чтобы прервать выполнение программы нажмите Ctrl+C')
    print()
    print("""
    Пример запроса:
    - Введите название вакансии: Программист Python
    - Введите местоположение на русском языке (страну, регион или город): Краснодарский край
    - За какой период искать (максимум 30 дней): 30
    - Показывать вакансии только с зарплатой (да/нет): нет
    - График работы (удаленная работа; полный день; сменный график; гибкий график.): удаленная работа
    
    Вакансии будут сохранены в папку "vacancies".
    """)
    while True:
        while True:
            vacancy = input('- Введите название вакансии: ')
            if not vacancy.isalpha():
                print('Название вакансии должно состоять только из букв.')
                continue
            break

        while True:
            location = input('- Введите местоположение на русском языке (страну, регион или город): ')
            if not location.isalpha():
                if '-' in location or ' ' in location:
                    pass
                else:
                    print('Название местоположения может состоять только из букв, знака дефиса и пробела.')
                    continue
            break
        while True:
            period = input('- За какой период искать (максимум 30 дней): ')
            if 0 < int(period) <= 30:
                break
            else:
                print('- Введите число от 1 до 30.')

        while True:
            need_salary = input('- Показывать вакансии только с зарплатой (да/нет): ')
            need_salary = need_salary.lower()
            if 'Да'.lower() in need_salary:
                need_salary = True
                break
            elif 'Нет'.lower() in need_salary:
                need_salary = False
                break
            else:
                print('- Введите "да" или "нет".')
        while True:
            schedule = input('- График работы (удаленная работа; полный день; сменный график; гибкий график'
                             ' ЛИБО нажмите ENTER, чтобы выбрать все графики работы): ')
            schedule = schedule.lower()
            if schedule in ('удаленная работа', 'полный день', 'сменный график', 'гибкий график,', ''):
                if 'удаленная работа' in schedule:
                    schedule = 'remote'
                    break
                elif 'полный день' in schedule:
                    schedule = 'fullDay'
                    break
                elif 'сменный график' in schedule:
                    schedule = 'shift'
                    break
                elif 'гибкий график' in schedule:
                    schedule = 'flexible'
                    break
                elif '' in schedule:
                    schedule = None
                    break
            else:
                print('- Введите что-то одно - "удаленная работа, полный день, сменный график, гибкий график" ')

        try:
            get_vacancies(vacancy=vacancy, location=location, period=period, need_salary=need_salary, schedule=schedule)
            break
        except:
            print()
            print('Скорей всего вы опечатались, попробуйте снова.')
            print()
            continue

    print('Окно закроется автоматически через 5 секунд.')
    time.sleep(5)


if __name__ == '__main__':
    main()
