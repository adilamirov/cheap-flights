FROM python:3.8-alpine

WORKDIR /app

RUN apk update && apk add postgresql-dev postgresql-client gcc python3-dev musl-dev g++

COPY requirements.txt requirements_dev.txt /tmp/
COPY ./app /app

RUN pip install --no-cache-dir -r /tmp/requirements_dev.txt

ENTRYPOINT ["./entrypoint.sh"]
