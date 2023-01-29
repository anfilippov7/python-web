# CRUD Docker-compose

Для запуска проекта (на ОС Linux) необходимо:

1. собрать контейнеры docker-compose командой:

sudo docker-compose build

2. выполнить запуск контейнеров:

sudo docker-compose up

3. применить миграции:

sudo docker-compose run --rm djangoapp python manage.py migrate

4. собрать статические файлы:

sudo docker-compose run --rm djangoapp python manage.py collectstatic

5. открыть приложение в браузере по адресу:

localhost:8000/api/v1/


