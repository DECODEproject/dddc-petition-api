FROM tiangolo/uvicorn-gunicorn-fastapi:python3.6

COPY ./app /app/app
COPY setup.py /

ARG DB_URL=sqlite:////app/app/db.sqlite3

RUN pip install --upgrade pip
RUN pip install -e /
RUN pip install email-validator
