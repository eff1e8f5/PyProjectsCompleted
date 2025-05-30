FROM python:3.12-alpine

ARG BOT_NAME=@MrClouds_sport_bot
ARG TOKEN=7196353599:AAFXJUbDptHxnSHPbsCL1AOqj7zgIt4mC6E
ARG DB_NAME=rtfest_summer_2024
ARG DB_HOST=172.17.0.3
ENV BOT_NAME="${BOT_NAME}"
ENV TOKEN="${TOKEN}"
ENV DB_NAME="${DB_NAME}"
ENV DB_HOST="${DB_HOST}"

ADD app /app
WORKDIR /app
RUN python -m venv .venv
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

# EXPOSE 8080

ENTRYPOINT [ "python", "main.py" ]
