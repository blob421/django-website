#!/bin/bash
echo "Waiting for Django DB check to pass..."

until python manage.py check --database default; do
  echo "Still waiting..."
  sleep 2
done

echo "Database is ready. Running migrations..."
python manage.py makemigrations
python manage.py migrate
python manage.py start_scheduler 


exec "$@"
