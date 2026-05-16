FROM python:3.12-slim
WORKDIR /app

COPY shared/ /app/shared/
COPY nsprovisioner/ /app/
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/app"

CMD ["python", "main.py"]