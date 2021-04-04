#!/bin/sh

HOST="pi@192.168.88.85"

for pyfile in amp*.py
do
  scp $pyfile ${HOST}:/home/pi/ampcontrol/
done

ssh ${HOST} sudo systemctl restart ampcontrol
