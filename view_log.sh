#!/bin/bash
pkill -9 logs.sh
./logs.sh&
tail -f logs.txt
