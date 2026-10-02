#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Применяю миграции базы данных..."
    alembic upgrade head
fi

exec "$@"
