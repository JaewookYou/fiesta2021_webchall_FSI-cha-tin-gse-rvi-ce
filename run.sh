#!/bin/bash
source ./setting.sh
while true
do
	docker-compose stop;docker-compose down;docker-compose rm -f;docker-compose build; docker-compose up -d;
	sleep 900
done
