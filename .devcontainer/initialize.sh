#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  cp .env.example .env
fi

docker compose -f docker-compose-local.yml build agent
