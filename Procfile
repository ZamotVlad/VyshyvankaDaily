web: gunicorn config.wsgi --worker-class gthread --threads 4 --log-file -
release: python manage.py migrate && python manage.py createcachetable