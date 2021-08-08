#!/bin/bash
mkdir -p /app/app/uploads/welcomebot/
wget http://arang.kr/welcomebot.png -O /app/app/uploads/welcomebot/welcomebot.png
python3 /app/app/app.py
