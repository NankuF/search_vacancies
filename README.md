## Сбор вакансий Headhunter в файл excel.

Скрипт составляет файл excel по вакансиям найденным на Headhunter.<br>

Данные  взяты с api Headhunter.<br>

### Требования:
*Если вы не на Windows, то вы и так знаете, что делать.*<br>

Для пользователей Windows:<br>
- У вас должен быть установлен python3. (проект написан на версии 3.10)<br>
Рядом с меню пуск есть поле поиска. Введите туда текст и нажмите enter.
    ```commandline
    powershell.exe
    ```
    В открывшимся окне введите:
    ```commandline
    python --version
    ```
    Если будет написана версия - все отлично, python установлен.<br>
    Если версия не указана - перейдите по ссылке и установите python:<br>
    ```commandline
    https://www.microsoft.com/store/productId/9PJPW5LDXLZ5
    ```
- Установите git:
    ```commandline
    https://github.com/git-for-windows/git/releases/download/v2.37.1.windows.1/Git-2.37.1-64-bit.exe
    ```
    Проверка git аналогична проверке python:<br>
    ```
    git --version
    ```
Установив python и git, вы выполнили все необходимые подготовительные работы.


### Установка:
Все дальнейшие команды вводятся в powershell на Windows или терминал на Unix.<br>
1. Скачайте проект:<br>

```commandline
git clone https://github.com/NankuF/search_vacancies.git
```

2. Перейдите в директорию:<br>

```commandline
cd search_vacancies
```
3. Создайте виртуальное окружение:<br>

```commandline
python -m venv venv
```
4. Активируйте окружение:
*Unix*
```commandline
. ./venv/bin/activate
```
*Windows*
При первом запуске Windows потребует расширить права. Введите следующий код в powershell и согласитесь со всем:<br>
```commandline
Set-ExecutionPolicy -ExecutionPolicy AllSigned -Scope CurrentUser
```
Введите следующий код:<br>
```commandline
. .\venv\Scripts\activate
```
Должно получиться так:
![img_1.png](img_1.png)
5. Установите зависимости:<br>

```commandline
pip install -r requirements.txt
```
5. Запуск:<br>
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

### Результат работы скрипта смотрите в папке `vacancies`