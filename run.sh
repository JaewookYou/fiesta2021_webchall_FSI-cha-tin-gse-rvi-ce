#!/bin/bash
source ./setting.sh
pkill logs
while true
do
	sudo rm -rf ./data/ext/ext_app/uploads/*
	sudo rm -rf ./data/int/int_app/uploads/*
	docker-compose stop;docker-compose down;docker-compose rm -f;docker network prune -f;docker-compose build; docker-compose up -d;docker volume prune -f;
	docker-compose logs -f >> logs.txt&
	date;
	sleep 1800;
done
