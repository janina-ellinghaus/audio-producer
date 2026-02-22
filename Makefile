.PHONY: *

dev:
	docker compose up --build --watch

clean:
	rm backend/__pycache__ -Rf
	docker system prune
