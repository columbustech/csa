#!/bin/bash
mkdir -p /storage/public/
(cd /ui && PUBLIC_URL="$CDRIVE_URL"app/"$COLUMBUS_USERNAME"/csa npm run build)
cp -r /ui/build/* /storage/public/
mkdir -p /storage/csa-data
service nginx start &
python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8001
