upload:
	- rm dist/*
	python3 -m build
	python3 -m twine upload --repository pypi dist/*

# Expect to see the output "[numpy]"
# Very simple test for a specific bug we encountered
dockerTest:
	e
	docker build -t alpine-python-benchify .
	docker run --rm alpine-python-benchify

pytest: ; pytest . -vv