FROM python:3.12-alpine
LABEL authors="zwickvitaly"

ENV PYTHONUNBUFFERED=1

WORKDIR /bot

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY bot .

ENTRYPOINT python3 main.py


