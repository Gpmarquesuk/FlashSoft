run:
	python run.py --spec examples/specs/sample_spec.yaml

docker-build:
	docker build -t flashsoft-autobot .

docker-run:
	docker run --rm -it --env-file .env flashsoft-autobot
