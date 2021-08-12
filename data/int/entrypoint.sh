#!/usr/bin/bash
mkdir -p /app/int_app/uploads/welcomebot/
wget http://arang.kr/bboot.jpeg -O /app/int_app/uploads/welcomebot/welcomebot.png
python3 /app/int_app/app.py
