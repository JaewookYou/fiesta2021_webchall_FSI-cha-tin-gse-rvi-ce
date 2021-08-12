#!/bin/bash
source ./setting.sh
while true
do
	rm -rf ./data/ext/ext_app/uploads/*
	rm -rf ./data/int/int_app/uploads/*
	docker-compose stop;docker-compose down;docker-compose rm -f;docker-compose build; docker-compose up -d;docker volume prune -f;
	date;
	sleep 1800;
done
