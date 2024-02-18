FROM python:3.11

# Копируем весь проект в контейнер
COPY . .

RUN apt-get update -y && apt-get upgrade -y && pip install --upgrade pip  \
    && pip install --upgrade setuptools  && apt-get install nano && apt-get install -y micro \
    && pip install -r requirements.txt \
    && apt-get clean



ENV PYTHONPATH $PYTHONPATH:.


CMD ["python3", "app.py"]