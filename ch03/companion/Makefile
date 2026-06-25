.PHONY: help up down logs smoke test clean rebuild ps spec

help:
	@echo "Targets:"
	@echo "  make up        # docker compose up -d (postgres + catalog + orders)"
	@echo "  make down      # docker compose down"
	@echo "  make clean     # docker compose down -v (drops all volumes)"
	@echo "  make logs      # follow logs"
	@echo "  make ps        # list running services"
	@echo "  make smoke     # run ./smoke_tests.sh against the running stack"
	@echo "  make test      # run pytest against the running stack"
	@echo "  make spec      # pretty-print the catalog OpenAPI document"
	@echo "  make rebuild   # rebuild catalog + orders images and restart"

up:
	docker compose up -d --build
	@echo "Waiting for the catalog service to be healthy..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do \
		if curl -sf http://localhost:8080/healthz >/dev/null 2>&1; then \
			echo "OK — catalog is up on http://localhost:8080"; break; \
		fi; \
		sleep 2; \
	done
	@echo "Waiting for the orders service to be healthy..."
	@for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do \
		if curl -sf http://localhost:8081/healthz >/dev/null 2>&1; then \
			echo "OK — orders is up on http://localhost:8081"; exit 0; \
		fi; \
		sleep 2; \
	done; \
	echo "orders did not become healthy in 30s"; exit 1

down:
	docker compose down

clean:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

smoke:
	./smoke_tests.sh

test:
	python -m pytest tests/ -v

spec:
	@curl -s http://localhost:8080/openapi.json | python -m json.tool

rebuild:
	docker compose build catalog orders
	docker compose up -d catalog orders
