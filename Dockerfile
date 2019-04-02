FROM python:3.7.2-alpine3.9

WORKDIR /app/

COPY src/requirements.txt .

RUN set -ex;\
  apk add --no-cache bash nginx; \
  mkdir /run/nginx /app/dist; \
  pip3 install -r requirements.txt;

COPY src .
RUN python update_website.py;

COPY srv/nginx.conf /etc/nginx/conf.d/fast-fala.conf
EXPOSE 80
STOPSIGNAL SIGTERM
CMD ["nginx", "-g", "daemon off;"]
