#!/usr/bin/bash
mkdir -p /app/int_app/uploads/welcomebot/
wget http://arang.kr/bboot.jpeg -O /app/int_app/uploads/welcomebot/welcomebot.png
rm /etc/localtime
ln -s /usr/share/zoneinfo/Asia/Seoul /etc/localtime
python3 /app/int_app/app.py
