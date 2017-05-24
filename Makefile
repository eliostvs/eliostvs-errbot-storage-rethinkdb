.PHONY: test all clean

DOCKER_IMAGE_NAME = errbot-rethinkdb-storage-plugin
PORT=28015

clean:
	@find . \( -iname "*.pyc" -o -iname "__pycache__" -o -iname "*.log" \) -print0 | xargs -0 rm -rf
	@rm -rf *.egg-info/ .coverage build/

db-up:
	docker run --name $(DOCKER_IMAGE_NAME) --rm -d -p 28015:28015 -p 8080:8080 rethinkdb:latest

db-stop:
	docker stop $(DOCKER_IMAGE_NAME) 2> /dev/null || echo "Image $(DOCKER_IMAGE_NAME) not found"

db-rm: db-stop
	docker rm $(DOCKER_IMAGE_NAME) 2> /dev/null || echo "Image $(DOCKER_IMAGE_NAME) not found"

db-logs:
	docker logs -f $(DOCKER_IMAGE_NAME)

db-clean: db-stop db-rm

db-all: db-clean db-up

db-port:
	@docker port $(DOCKER_IMAGE_NAME) $(PORT) | cut -f 2 -d :

test: clean
	@PYTHONPATH=$(CURDIR) pytest $(test) --port=$(shell docker port $(DOCKER_IMAGE_NAME) $(PORT) | cut -f 2 -d :)

install:
	pip install -r dev-requirements.txt
