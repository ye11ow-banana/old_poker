FROM python:3.11

ENV POETRY_VERSION=1.4.0
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache
ENV PATH="${PATH}:${POETRY_VENV}/bin"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app/src"

RUN pip install --upgrade pip
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

WORKDIR /usr/src/app

COPY . /usr/src/app
RUN poetry install

EXPOSE 8000

CMD ["poetry", "run", "alembic", "upgrade", "head"]
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
