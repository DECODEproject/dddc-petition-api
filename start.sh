#!/bin/sh


if ! [ -x "$(command -v zenroom)" ]; then
  echo 'Error: zenroom is not installed. Please install it and put it on PATH before continue' >&2
  exit 1
fi

cd app/credentials
bash generate_credentials.sh
cd ../..
docker build -t dddc-petition-api .
docker run --rm -p 80:80 -e APP_MODULE="app.main:api" -e LOG_LEVEL="debug" -it dddc-petition-api
