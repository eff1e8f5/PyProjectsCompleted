FROM python:3.11-slim

ADD app /app
WORKDIR /app
EXPOSE 8000

RUN apt update && apt install -y && apt install gcc -y
RUN python -m venv venv
RUN python -m pip install pip -U && pip install -r requirements.txt
CMD python main.py
