FROM python:3.8-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt update && apt install -y build-essential

RUN python -m pip install --upgrade pip \
 && python -m pip install "poetry==1.4.0"

WORKDIR /code
ADD pyproject.toml poetry.lock /code/
ADD pyproject.toml /code/
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-interaction --no-root

ADD misc/dokku/CHECKS /app/
ADD misc/dokku/* /code/

WORKDIR /code

COPY . /code/
RUN /code/manage.py collectstatic --noinput
