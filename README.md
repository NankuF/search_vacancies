## Рассылка резюме, сбор вакансий и ключевых навыков в Headhunter
#### UPD 17.09.2022: приложение работает только с GUI, т.к. требуется авторизация пользователя в браузере с поддержкой javascript.
Если вы желаете получить только список вакансий и ключевые навыки - проще всего запустить файлы с расширением `exe` под Windows из папки `for windows`.

### Возможности приложения
1. Сбор вакансии в файл excel.
   <details>
     <summary>Фото</summary>
      <img src="img.png">
   </details>

2. Сбор ключевых навыков в файл txt.
   <details>
     <summary>Фото</summary>
      <img src="img_1.png">
   </details>

3. Рассылка резюме по собранным вакансиям.

### Требования для разработчиков:
- Python 3.8.
- git.
- созданное приложение на [dev.hh.ru](https://dev.hh.ru/admin).
- файл `.env` с секретными ключами.
### Запуск под Windows:<br>
  - Скачайте и запустите .exe файлы.<br>
  Собрать вакансии - [скачать](https://github.com/NankuF/search_vacancies/raw/master/for%20windows/get_vacancies.exe)<br>
  Собрать ключевые навыки - [скачать](https://github.com/NankuF/search_vacancies/raw/master/for%20windows/get_skills.exe)<br>
  Рассылка резюме - не реализована под Windows.


### Установка приложения в Unix:

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

4. Активируйте окружение:<br>

```commandline
. ./venv/bin/activate
```
5. Установите зависимости:<br>

```commandline
pip install -r requirements.txt
```
6. Создайте приложение на [dev.hh.ru](https://dev.hh.ru/admin).
7. Добавьте файл .env. В нем укажите данные вашего приложения `CLIENT_ID` и `CLIENT_SECRET`.
Остальные данные добавятся автоматически после авторизации.
```text
CLIENT_ID=client_id_in_your_app
CLIENT_SECRET=client_secret_in_your_app

APP_ACCESS_TOKEN=will be added automatically after authorization
USER_ACCESS_TOKEN=will be added automatically after authorization
USER_REFRESH_TOKEN=will be added automatically after authorization
```

## Запуск
### Сбор вакансий и ключевых навыков
   `--vacancy` - Название вакансии.<br>
   `--location`- Можно ввести город, регион или страну.<br>
   `--need_salary` - Укажите этот ключ, если хотите увидеть вакансии с указанной зарплатой.<br>
   `--period` - За какой период искать работу. Указать количество дней. Максимум 30.<br>
   `--schedule` - График работы: remote | fullDay | shift | flexible (
   удаленная работа; полный день; сменный график; гибкий график).
   Этот ключ можно не указывать.<br>
   **Вакансии сохраняются в папке `vacancies`**<br>
   **Ключевые навыки сохраняются в папке `skills`**<br>
```commandline
python main.py --vacancy "Программист Python" --location "Санкт-Петербург" --need_salary --period 30 --schedule "remote"

```

```commandline
python main.py --vacancy "Уборщица" --location "Краснодарский край" --period 7

```

```commandline
python main.py --vacancy "Прораб" --location "Россия" --period 1

```

### Рассылка резюме
```commandline
python apply_vacancies.py
```
