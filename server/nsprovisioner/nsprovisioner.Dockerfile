FROM python:3.12-slim
WORKDIR /app

# install system dependencies for redis and supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-server supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY nsprovisioner/ /app/
COPY requirements.txt /app/requirements.txt
# copy multi-process supervisor engine configuration
COPY nsprovisioner/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
# gRPC / telemetry hooks run here
EXPOSE 50051

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]