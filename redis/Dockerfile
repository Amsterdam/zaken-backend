FROM redis:6.0.9-alpine

RUN apk add --no-cache gettext
COPY redis.conf.template /usr/local/etc/redis/redis.conf.template

CMD envsubst < /usr/local/etc/redis/redis.conf.template > /usr/local/etc/redis/redis.conf && exec redis-server /usr/local/etc/redis/redis.conf
