FROM python:3
WORKDIR /code
COPY code /code/
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
EXPOSE 8080
CMD ["/code/runSync.sh"]