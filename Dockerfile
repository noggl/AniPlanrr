FROM python:3
WORKDIR /code
COPY ./requirements.txt /code/
COPY ./runSync.sh /code/
COPY ./AniListSonarrSync.py /code/
RUN pip install -r requirements.txt
CMD ["/code/runSync.sh"]