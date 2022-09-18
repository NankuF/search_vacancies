FROM python:alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY .env .env
COPY . .

CMD ["python", "apply_vacancies.py"]