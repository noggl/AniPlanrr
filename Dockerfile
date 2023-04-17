FROM python:3
WORKDIR /code
COPY code/requirements.txt /code/
COPY code/runSync.sh /code/
COPY code/aniplanrr.py /code/
RUN pip install -r requirements.txt
CMD ["/code/runSync.sh"]