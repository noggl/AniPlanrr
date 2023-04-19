FROM python:3
WORKDIR /code
COPY code /code/
RUN pip install -r requirements.txt
CMD ["/code/runSync.sh"]