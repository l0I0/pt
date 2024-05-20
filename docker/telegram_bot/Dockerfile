FROM python:3.9-slim

COPY ./requirements.txt /app/.

RUN pip install -r /app/requirements.txt

COPY py-telegram-bot.py /app/.
WORKDIR /app


CMD ["python", "py-telegram-bot.py"]