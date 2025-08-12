install:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

setup-check:
	python setup.py

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	celery -A app.celery_app.celery_app worker --loglevel=INFO

test:
	pytest -q

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
