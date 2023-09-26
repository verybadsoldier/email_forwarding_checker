FROM python:3.9.18-alpine3.18

COPY . /app

RUN apk add git

RUN pip install --upgrade pip && cd /app && pip install .

CMD email_forwarding_checker --version
