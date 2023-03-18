.PHONY: update-deps check run clean

update-deps:
	poetry update

setup: poetry.lock
	poetry install

check:
	pre-commit run --all-files

run:
	poetry run neilbot

clean:
	rm -rf **/__pycache__ .mypy_cache
