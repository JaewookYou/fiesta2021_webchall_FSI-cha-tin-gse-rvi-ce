FROM ubuntu:latest
WORKDIR /app
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential libcurl4-openssl-dev libssl-dev
RUN apt-get install -y net-tools procps
RUN python3 -m pip install pymysql cryptography
ENTRYPOINT /app/entrypoint.sh && /bin/bash
CMD ["true"]
