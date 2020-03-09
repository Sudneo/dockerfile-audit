# FROM localhost:5000/myimage@sha256:47bfdb88c3ae13e488167607973b7688f69d9e8c142c2045af343ec199649c09
FROM debian:buster-slim AS build
#FROM https://test-123.com/image AS test

LABEL multi.label1="value1" \
      multi.label2="value2" \
      other="value3"

LABEL "com.example.vendor"="ACME Incorporated"
LABEL com.example.label-with-value="foo"
LABEL version="1.0"
LABEL description="This text illustrates \
that label-values can span multiple lines."


#
# LABEL maintainer="NGINX Docker Maintainers <docker-maint@nginx.com>"
#
# ENV NGINX_VERSION   1.17.9
# ENV NJS_VERSION     0.3.9
# ENV PKG_RELEASE     1~buster
#
 RUN set -x \
     && addgroup --system --gid 101 nginx \  
     && adduser --system --disabled-login --ingroup nginx --no-create-home --home /nonexistent \
    --gecos "nginx user" --shell /bin/false --uid 101 nginx
RUN ["id", "test","test2" , "test4"]

FROM http://test-123.com:4682/image AS test

USER testuser:www-data

USER root:root

USER 0:0

USER root

USER 1000
