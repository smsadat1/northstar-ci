# Download stage 1
FROM debian:bookworm-slim AS downloader
RUN apt-get update && apt-get install -y wget tar
RUN wget https://github.com/containerd/nerdctl/releases/download/v1.7.0/nerdctl-1.7.0-linux-amd64.tar.gz \
    && tar Cxzf /usr/local/bin nerdctl-1.7.0-linux-amd64.tar.gz

# Download stage 2
FROM python:3.12-slim 
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Copy nerdctl from the downloader stage to your final image
COPY --from=downloader /usr/local/bin/nerdctl /usr/local/bin/nerdctl

RUN apt-get update && apt-get install -y \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/* 

COPY ./shared /app/shared
COPY ./nsrunner /app/nsrunner

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "-m", "nsrunner.main"]