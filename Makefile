.PHONY: help test clean merge diff take

help:
	@echo "  make test             - Run tests using ~/temp folder"
	@echo "  make clean            - Clean up temporary test files"
	@echo "  make merge <specs_path>  - Merge templates (repo is .); e.g. make merge ../Specifications"
	@echo "  make diff <filespec>  - Diff temp vs expected for a single file"
	@echo "  make take <filespec>  - Overwrite expected file with temp file"

test:
	@TEMP_REPO="$$HOME/tmp/testRepo"; \
	echo "Setting up temporary testing folder at $$TEMP_REPO..."; \
	rm -rf "$$TEMP_REPO"; \
	mkdir -p "$$TEMP_REPO"; \
	cp -r . "$$TEMP_REPO"
	@echo "Debug: Checking specifications structure..."; \
	find .stage0_template/Specifications -name "*.yaml" | head -10
	@echo "Running the container..."; \
	LOG_LEVEL="$${LOG_LEVEL:-DEBUG}"; \
	docker run --rm \
		-v "$$HOME/tmp/testRepo:/repo" \
		-v "$$(pwd)/.stage0_template/specifications:/specifications" \
		-e LOG_LEVEL="$$LOG_LEVEL" \
		-e SERVICE_NAME="sample" \
		ghcr.io/agile-learning-institute/stage0_runbook_merge:latest
	@echo "Removing __pycache__ from both sides before diff..."; \
	find "$$HOME/tmp/testRepo" -type d -name __pycache__ -print0 2>/dev/null | xargs -0 rm -rf 2>/dev/null || true; \
	find "$$(pwd)/.stage0_template/test_expected" -type d -name __pycache__ -print0 2>/dev/null | xargs -0 rm -rf 2>/dev/null || true
	@echo "Checking output (ignoring .git, .DS_Store, node_modules, dist)..."; \
	(diff -qr "$$(pwd)/.stage0_template/test_expected/" "$$HOME/tmp/testRepo/" 2>/dev/null || true) | (grep -v '\.git' | grep -v '\.DS_Store' | grep -v 'node_modules' | grep -v 'dist' | grep -v 'playwright-report' | grep -v 'test-results' || true) > /tmp/stage0_diff.txt; \
	if [ -s /tmp/stage0_diff.txt ]; then cat /tmp/stage0_diff.txt; echo "Fail: unexpected differences."; exit 1; fi; \
	echo "Done."

clean:
	@echo "Removing temporary test repo at $$HOME/tmp/testRepo..."; \
	rm -rf "$$HOME/tmp/testRepo"

merge:
	@CONTEXT_PATH="$(firstword $(filter-out $@,$(MAKECMDGOALS)))"; \
	if [ -z "$$CONTEXT_PATH" ]; then \
		echo "Usage: make merge /path/to/Specifications"; \
		exit 1; \
	fi; \
	if [ ! -d "$$CONTEXT_PATH" ]; then \
		echo "Error: $$CONTEXT_PATH does not exist or is not a directory"; \
		exit 1; \
	fi; \
	echo "Running merge with specifications from $$CONTEXT_PATH"; \
	LOG_LEVEL="$${LOG_LEVEL:-INFO}"; \
	docker run --rm \
		-v "$$(pwd):/repo" \
		-v "$$CONTEXT_PATH:/specifications" \
		-e LOG_LEVEL="$$LOG_LEVEL" \
		-e SERVICE_NAME="$$SERVICE_NAME" \
		ghcr.io/agile-learning-institute/stage0_runbook_merge:latest

diff:
	@FILESPEC="$(firstword $(filter-out diff,$(MAKECMDGOALS)))"; \
	if [ -z "$$FILESPEC" ]; then \
		echo "Usage: make diff <filespec>  (e.g. make diff DeveloperEdition/mh)"; \
		exit 1; \
	fi; \
	TEMP="$$HOME/tmp/testRepo/$$FILESPEC"; \
	EXP="$(PWD)/.stage0_template/test_expected/$$FILESPEC"; \
	if [ ! -f "$$TEMP" ]; then echo "Temp file not found: $$TEMP"; exit 1; fi; \
	if [ ! -f "$$EXP" ]; then echo "Expected file not found: $$EXP"; exit 1; fi; \
	diff "$$TEMP" "$$EXP"

take:
	@FILESPEC="$(firstword $(filter-out take,$(MAKECMDGOALS)))"; \
	if [ -z "$$FILESPEC" ]; then \
		echo "Usage: make take <filespec>  (e.g. make take DeveloperEdition/mh)"; \
		exit 1; \
	fi; \
	TEMP="$$HOME/tmp/testRepo/$$FILESPEC"; \
	EXP="$(PWD)/.stage0_template/test_expected/$$FILESPEC"; \
	if [ ! -f "$$TEMP" ]; then echo "Temp file not found: $$TEMP"; exit 1; fi; \
	cp "$$TEMP" "$$EXP"; \
	echo "Updated $$EXP from $$TEMP"

%:
	@:
