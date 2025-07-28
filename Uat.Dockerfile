############################################
# Dockerfile to build elasticsearch_service microservice
# Based on python ECR hub image
############################################

# Set base image to python
#FROM 078398740737.dkr.ecr.us-west-2.amazonaws.com/repository-h1fytp6aeclu:8eaa2fe3
FROM public.ecr.aws/docker/library/python:3.11.9-slim

# File Author / Maintainer
LABEL maintainer="Shamsher Kushwaha <shamsher.kushwaha@nmgtechnologies.com>"

# Copy source file and python req's
COPY . /usr/src/
COPY app/requirements.txt /
RUN rm -rf /usr/src/app/.env 
COPY config/.env.uat /usr/src/app/.env 

# Install requirements
WORKDIR /usr/src/app/
RUN apt update
RUN apt install gcc build-essential python3-dev awscli curl sqlite3 -y
RUN pip install env 
RUN python -m venv env
RUN pip install -r requirements.txt

# Setup nginx
RUN curl https://nginx.org/keys/nginx_signing.key | gpg --dearmor \
    | tee /usr/share/keyrings/nginx-archive-keyring.gpg >/dev/null
RUN gpg --dry-run --quiet --no-keyring --import --import-options import-show /usr/share/keyrings/nginx-archive-keyring.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
http://nginx.org/packages/debian `lsb_release -cs` nginx" \
    | tee /etc/apt/sources.list.d/nginx.list
RUN apt update
RUN apt install nginx  -y
RUN rm /etc/nginx/conf.d/default.conf
ADD config/flask.conf /etc/nginx/conf.d/
RUN echo "daemon off;" >> /etc/nginx/nginx.conf


# Setup supervisord
RUN mkdir -p /usr/local/etc/supervisord/{conf-available,conf-enabled}
RUN mkdir /var/log/supervisord
RUN mkdir /var/run/supervisord
#ADD config/gunicorn_logging.conf .
ADD config/supervisord.conf /usr/local/etc/supervisord.conf
RUN mkdir -p /var/log/supervisor
ADD config/nginx-supervisord.conf /usr/local/etc/supervisord/conf-enabled/
ADD config/gunicorn.conf /usr/local/etc/supervisord/conf-enabled/
COPY config/profile-uat.sh /srv/
RUN chmod +x /srv/profile-uat.sh 
ADD config/initial-uat.sh /usr/bin/initial
RUN chmod +x /usr/bin/initial
ENTRYPOINT [ "initial" ]
