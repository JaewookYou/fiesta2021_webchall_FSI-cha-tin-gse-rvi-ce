#!/bin/bash
while true
do
	date >> logs.txt
	docker-compose logs -f >> logs.txt
	sleep 2
done
