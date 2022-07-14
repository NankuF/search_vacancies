## Сбор вакансий Headhunter в файл excel.

Скрипт составляет файл excel по вакансиям найденным на Headhunter.<br>

Данные  взяты с api Headhunter.<br>

### Установка:
1. Скачайте проект:<br>

```commandline
git clone https://github.com/NankuF/search_vacancies.git
```

2. Создайте виртуальное окружение:<br>

```commandline
python -m venv venv
```

3. Перейдите в директорию:

```commandline
cd search_vacancies
```

4. Установите зависимости:<br>

```commandline
pip install -r requirements.txt
```
5. Запуск:
`--vacancy` - Название вакансии.<br>
`--location`- Можно ввести город, регион или страну.<br>
`--need_salary` - Укажите этот ключ, если хотите увидеть вакансии с указанной зарплатой.<br>
`--period` - За какой период искать работу. Указать количество дней. Максимум 30.<br>
`--schedule` - График работы: remote | fullDay | shift | flexible (
                             удаленная работа; полный день; сменный график; гибкий график). 
                             Этот ключ можно не указывать.
```commandline
python main.py --vacancy "Программист Python" --location "Санкт-Петербург" --need_salary --period 30 --schedule "remote"

```

```commandline
python main.py --vacancy "Уборщица" --location "Краснодарский край" --period 7

```

```commandline
python main.py --vacancy "Прораб" --location "Россия" --period 1

```

*Скорректированная зарплата считается так:*<br>
Если в вакансии указана только `зарплата от`:
`зарплата от * 1.2`<br>
Если в вакансии указана только `зарплата до`:
`зарплата до * 0.8`<br>
Если в вакансии указана `зарплата от и до`:
`(зарплата от + зарплата до) / 2`<br>
К рублю зарплата приводится по курсу, указанному в api hh. Он может отличаться от текущего курса.
