ifeq ($(shell test -e '.env' && echo -n yes),yes)
	include .env
endif

BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

HELP_FUN = \
    %help; \
    printf "\n${BLUE}Usage:${RESET}\n  make ${YELLOW}<target>${RESET}\n\n"; \
    while(<>) { \
        if(/^([a-zA-Z0-9_-]+):.*\#\#(?:@([a-zA-Z0-9_-]+))?\s(.*)$$/) { \
            push(@{$$help{$$2 // 'Other'}}, [$$1, $$3]); \
        } \
    }; \
    printf "${BLUE}Targets:${RESET}\n"; \
    for (sort keys %help) { \
        printf "${GREEN}%s:${RESET}\n", $$_; \
        printf "  %-20s %s\n", $$_->[0], $$_->[1] for @{$$help{$$_}}; \
        print "\n"; \
    }

args := $(wordlist 2, 100, $(MAKECMDGOALS))
ifndef args
	MESSAGE = "No such command (or you pass two or many targets to ). List of possible commands: make help"
else
	MESSAGE = "Done"
endif
env: ##@Utils Prepare .env file
	cp .env.example .env

up-app: ##@Run Run all docker compose
	docker compose up --build -d --remove-orphans

k6-load-test: ##@Run Run k6 load testing
	docker compose -f "docker-compose-k6.yaml" run k6 run --out json=test_results.json /scripts/load-test.js

drop-load-testing:
	docker compose -f "docker-compose-k6.yaml" down -v
drop-app: 
	docker compose down -v

drop-all: ##@Cleanup Clear all docker info
	make drop-load-testing
	make drop-app

stop-slave1:  ##@Utils Stop slave 1
	docker compose down postgres-slave1
stop-slave2: ##@Utils Stop slave 2
	docker compose down postgres-slave2

stop-app1: ##@Utils Stop app 2
	docker compose down app1
stop-app2: ##@Utils Stop app 2
	docker compose down app2

clear-output: ##@Cleanup Clear k6 output
	rm -f k6/output/summary.html
	rm -f k6/output/test_results.json

run-preset1: up-app ##@Presets Run preset 1 (nothing disabled)
	make k6-load-test
	cp k6/output/summary.html "results/k6_disabled[none].html"
	make clear-output
	make drop-all

run-preset2: up-app  ##@Presets Run preset 2 (disable slave1)
	make stop-slave1
	make k6-load-test
	cp k6/output/summary.html "results/k6_disabled[slave1].html"
	make clear-output
	make drop-all

run-preset3: up-app  ##@Presets Run preset 3 (disable slave1, app1)
	make stop-slave1
	make stop-app1
	make k6-load-test
	cp k6/output/summary.html "results/k6_disabled[slave1,app1].html"
	make clear-output
	make drop-all

.PHONY: help
help: ##@Help Show this help
	@echo -e "Usage: make [target] ...\n"
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)

%::
	echo $(MESSAGE)