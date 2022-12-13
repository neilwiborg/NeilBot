FROM python:3.10
WORKDIR /bot
COPY . /bot
RUN apt-get update -qq && apt-get install ffmpeg -y
RUN pip install -U poetry
RUN make setup
CMD make run
