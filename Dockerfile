FROM tiangolo/uwsgi-nginx:python3.6

ADD . /code
WORKDIR /code

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN chmod +rwx /etc/ssl/openssl.cnf
RUN sed -i 's/TLSv1.2/TLSv1/g' /etc/ssl/openssl.cnf
RUN sed -i 's/SECLEVEL=2/SECLEVEL=1/g' /etc/ssl/openssl.cnf

ENV LISTEN_PORT $LISTEN_PORT
ENV UWSGI_INI $UWSGI_INI
ENV PYTHONPATH $PYTHONPATH
ENV NGINX_WORKER_PROCESSES auto
ENV NGINX_WORKER_CONNECTIONS 65535
ENV UWSGI_PROCESSES 3


EXPOSE 5000
EXPOSE 1717
