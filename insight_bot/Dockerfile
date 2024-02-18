FROM python:3.10

# Копируем весь проект в контейнер
COPY . .


RUN apt-get update -y && apt-get upgrade -y && apt-get install nano -y && pip install --upgrade pip  \
    && apt-get install -y micro  \
    && pip install --upgrade setuptools && pip install mutagen \
    && pip install -r requirements.txt && apt-get install -y ffmpeg  \
    && apt-get clean



ENV PYTHONPATH $PYTHONPATH:.

CMD ["python3", "bot.py"]