# Use the base image with Python and nginx/uwsgi
FROM tiangolo/uwsgi-nginx:python3.6

# Copy the application code to the container
ADD . /code

# Set the working directory
WORKDIR /code

# Copy .env file to the container
COPY .env /code

# Upgrade pip and install requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

# Change permissions and update OpenSSL configuration
RUN chmod +rwx /etc/ssl/openssl.cnf \
    && sed -i 's/TLSv1.2/TLSv1/g' /etc/ssl/openssl.cnf \
    && sed -i 's/SECLEVEL=2/SECLEVEL=1/g' /etc/ssl/openssl.cnf

# Set environment variables
ENV LISTEN_PORT=5000 \
    UWSGI_INI=/code/uwsgi/uwsgi.ini \
    PYTHONPATH=/code/app \
    NGINX_WORKER_PROCESSES=auto \
    NGINX_WORKER_CONNECTIONS=65535 \
    UWSGI_PROCESSES=4

# Expose ports
EXPOSE 5000
EXPOSE 1717
