upload:
	- rm dist/*
	python3 -m build
	python3 -m twine upload --repository pypi dist/*

dockerTest:
	docker build -t alpine-python-benchify .
	docker run --rm alpine-python-benchify