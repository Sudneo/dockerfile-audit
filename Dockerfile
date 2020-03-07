# FROM localhost:5000/myimage@sha256:47bfdb88c3ae13e488167607973b7688f69d9e8c142c2045af343ec199649c09
FROM debian:buster-slim AS build
#FROM https://test-123.com/image AS test

#
# LABEL maintainer="NGINX Docker Maintainers <docker-maint@nginx.com>"
#
# ENV NGINX_VERSION   1.17.9
# ENV NJS_VERSION     0.3.9
# ENV PKG_RELEASE     1~buster
#
 RUN set -x \
     && addgroup --system --gid 101 nginx \  
     && adduser --system --disabled-login --ingroup nginx --no-create-home --home /nonexistent\  
--gecos "nginx user" --shell /bin/false --uid 101 nginx   \    

id
FROM http://test-123.com:4682/image AS test

USER daniele:daniele

USER root:root

USER 0:0

USER root

USER 1000
