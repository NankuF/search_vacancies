"""
Вариант скрипта для компиляции в .exe
Использование на свой страх и риск, на ошибки и баги не проверялось.
"""
import time

from main import run_skills_counter


def main():
    print('Чтобы прервать выполнение программы нажмите Ctrl+C')
    print()
    print("""
       Пример запроса:
       - Введите название вакансии: Программист Python
       - Введите местоположение на русском языке (страну, регион или город): Краснодарский край

       Ключевые навыки будут сохранены в папку "skills".
       """)
    while True:
        while True:
            vacancy = input('- Введите название вакансии: ')
            if not vacancy.isalpha():
                if '-' in vacancy or ' ' in vacancy:
                    pass
                else:
                    print('Название вакансии может состоять только из букв, знака дефиса и пробела.')
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

        try:
            run_skills_counter(vacancy, location, period=30)
            break
        except:
            print()
            print('Скорей всего вы опечатались, попробуйте снова.')
            print()
            continue

    print('Окно закроется автоматически через 3 секунды.')
    time.sleep(3)


if __name__ == '__main__':
    main()
