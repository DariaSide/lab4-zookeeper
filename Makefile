.PHONY: build ensemble status quorum-test ephemeral-test demo-unfenced demo-fenced verify down clean

build:
	docker compose --profile coordinators build

ensemble:
	docker compose up -d zk1 zk2 zk3

status:
	./scripts/status.sh

quorum-test:
	./scripts/quorum-test.sh

ephemeral-test:
	./scripts/ephemeral-test.sh

demo-unfenced:
	./scripts/failover-demo.sh unfenced

demo-fenced:
	./scripts/failover-demo.sh fenced

verify:
	./scripts/verify.sh

down:
	docker compose --profile coordinators down

clean:
	docker compose --profile coordinators down -v
	rm -f logs/*.log logs/*.txt runtime/last-*-run
