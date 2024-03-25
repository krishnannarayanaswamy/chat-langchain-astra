FROM python:3.11
ENV PYTHONUNBUFFERED True

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r  requirements.txt

ENV APP_HOME /root
WORKDIR $APP_HOME
COPY ./backend/*.py $APP_HOME/backend/

EXPOSE 8080
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port 8080
