FROM ubuntu:latest
WORKDIR /app/int_app
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential libcurl4-openssl-dev libssl-dev
RUN apt-get install -y net-tools procps wget systemd
RUN python3 -m pip install pymysql cryptography
RUN groupadd -g 999 user
RUN useradd -r -u 999 -g user user
USER user
ENTRYPOINT /app/entrypoint.sh && /bin/bash
CMD ["true"]
