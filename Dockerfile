FROM python:3
WORKDIR /code
COPY code /code/
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y nginx
EXPOSE 8080
CMD ["/code/runSync.sh"]