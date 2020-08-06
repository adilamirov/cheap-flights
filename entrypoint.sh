#!/bin/sh

set -e

while ! pg_isready -h postgres -p 5432 > /dev/null 2> /dev/null; do
    echo "Waiting for postgres..."
    sleep 3
done
echo "PostgreSQL started"

python -m app.db --pg-url postgres://postgres:postgres@postgres:5432/flights upgrade head

exec "$@"
