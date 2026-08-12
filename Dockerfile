FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN apt update && apt install -y build-essential

RUN python -m pip install --upgrade pip \
 && python -m pip install "uv==0.11.6"

WORKDIR /code
ADD pyproject.toml uv.lock /code/
# Install into the system Python so /usr/local/bin/uwsgi (misc/dokku/Procfile)
# keeps working.
ENV UV_PROJECT_ENVIRONMENT=/usr/local
# requires-python is ">=3.13,<4" and there is no .python-version in the image,
# so uv could pick a different managed interpreter (e.g. 3.14 or a 3.15
# preview) than the image's Python 3.13. Force uv to use the image's own
# interpreter instead of a downloaded managed one.
ENV UV_PYTHON_DOWNLOADS=never
# --locked: the lock deliberately holds older versions; a re-lock must error.
RUN uv sync --locked --no-group dev --no-install-project

ADD misc/dokku/CHECKS /app/
ADD misc/dokku/* /code/

WORKDIR /code

COPY . /code/
RUN /code/manage.py collectstatic --noinput
