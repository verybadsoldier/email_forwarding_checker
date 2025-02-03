FROM python:3.12-alpine

COPY . /app

RUN apk add git

RUN pip install --upgrade pip && cd /app && pip install .

CMD email_forwarding_checker --config_file /config.yml --daemon
