FROM python:3.12-slim

WORKDIR /app/src

COPY requirements.txt /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD ["flask", "run", "--host=0.0.0.0"]

