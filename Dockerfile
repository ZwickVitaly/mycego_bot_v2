FROM python:3.12-alpine
LABEL authors="zwickvitaly"

ENV PYTHONUNBUFFERED=1

WORKDIR /bot

COPY pyproject.toml poetry.lock ./
RUN pip install poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY gc.json gc.json

COPY bot .

ENTRYPOINT alembic upgrade head && python3 main.py


