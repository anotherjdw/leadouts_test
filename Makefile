.PHONY: install test test-unit test-integration test-e2e lint format typecheck check fmt plan package clean

install:
	pip install -e ".[dev]"

test:
	pytest

test-unit:
	pytest tests/unit

test-integration:
	pytest tests/integration

test-e2e:
	pytest tests/end_to_end

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

check: lint typecheck test

fmt:
	terraform fmt -recursive infra/terraform/

plan:
	terraform -chdir=infra/terraform plan

package:
	mkdir -p lib
	rm -f lib/leadouts_test.zip
	cd src && find leadouts_test -type f \
	  -not -path '*/__pycache__/*' \
	  -not -path 'leadouts_test/contracts/*' \
	  -not \( -path '*/jobs/*' -name '*.yaml' \) \
	  | zip -q -X "$(CURDIR)/lib/leadouts_test.zip" -@

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
