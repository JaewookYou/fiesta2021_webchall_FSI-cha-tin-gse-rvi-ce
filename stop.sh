#!/bin/bash
pkill sleep
pkill run.sh
pkill logs
sudo rm -rf ./data/ext/ext_app/uploads/*
sudo rm -rf ./data/int/int_app/uploads/*
docker-compose stop;docker-compose down;docker-compose rm -f;

