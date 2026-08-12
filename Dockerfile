FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt update && apt install -y build-essential

RUN python -m pip install --upgrade pip \
 && python -m pip install "uv==0.11.6"

WORKDIR /code
ADD pyproject.toml uv.lock /code/
# Install into the system Python so /usr/local/bin/uwsgi (misc/dokku/Procfile)
# keeps working.
ENV UV_PROJECT_ENVIRONMENT=/usr/local
# requires-python is ">=3.9,<4" and there is no .python-version in the image,
# so uv would pick the newest interpreter it can download (3.13/3.14), on
# which Django 2.0 cannot run. Force uv to use the image's own Python 3.9
# instead of a downloaded managed interpreter.
ENV UV_PYTHON_DOWNLOADS=never
# --locked: the lock deliberately holds older versions; a re-lock must error.
RUN uv sync --locked --no-group dev --no-install-project

ADD misc/dokku/CHECKS /app/
ADD misc/dokku/* /code/

WORKDIR /code

COPY . /code/
RUN /code/manage.py collectstatic --noinput
