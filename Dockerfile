FROM python:3.7.2-alpine3.9

WORKDIR /app/

COPY src/requirements.txt .

RUN set -ex ;\
  apk add --no-cache bash nginx; \
  mkdir /run/nginx; \
  pip3 install -r requirements.txt;

COPY srv/nginx.conf /etc/nginx/conf.d/fast-fala.conf
COPY src .

EXPOSE 80

STOPSIGNAL SIGTERM

CMD ["nginx", "-g", "daemon off;"]