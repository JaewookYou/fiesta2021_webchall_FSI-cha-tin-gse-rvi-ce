FROM ubuntu:latest
WORKDIR /app/ext_app
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential
RUN apt-get install -y net-tools procps
RUN python3 -m pip install flask flask_socketio
RUN groupadd -g 999 user
RUN useradd -r -u 999 -g user user
USER user
ENTRYPOINT /app/entrypoint.sh && /bin/bash
CMD ["true"]
