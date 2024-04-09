# syntax=docker/dockerfile:1

FROM tiangolo/uwsgi-nginx:python3.6

ARG LISTEN_PORT=5000
ARG UWSGI_INI=/code/uwsgi/uwsgi.ini
ARG PYTHONPATH=/code/app

ENV LISTEN_PORT=$LISTEN_PORT
ENV UWSGI_INI=$UWSGI_INI
ENV PYTHONPATH=$PYTHONPATH
ENV NGINX_WORKER_PROCESSES auto
ENV NGINX_WORKER_CONNECTIONS 65535
ENV UWSGI_PROCESSES 3

ADD . /code
WORKDIR /code

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    chmod +rwx /etc/ssl/openssl.cnf && \
    sed -i 's/TLSv1.2/TLSv1/g' /etc/ssl/openssl.cnf && \
    sed -i 's/SECLEVEL=2/SECLEVEL=1/g' /etc/ssl/openssl.cnf

EXPOSE $LISTEN_PORT
EXPOSE 1717

CMD ["python", "manage.py"]
