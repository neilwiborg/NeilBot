FROM python:3.10
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
RUN apt-get update -qq && apt-get install ffmpeg -y
COPY . /bot
CMD python neilbot/bot.py
