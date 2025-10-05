# Luminate AI Integration Tests

## Overview

This directory contains integration tests to validate the data pipeline and prevent regressions before moving to new development phases.

## Test Suite: `test_integration.py`

Comprehensive integration tests covering:

1. **Data Directory Exists** - Verifies processed data directory
2. **JSON Files Count** - Validates 593 expected output files
3. **Course ID Correctness** - Ensures all files use COMP237 course ID `_11378_1`
4. **URL Format Validation** - Checks Blackboard Ultra URL patterns
5. **Chunk Structure Validation** - Verifies chunk fields and token counts
6. **Graph Relationships** - Validates 1,296 relationship links
7. **Metadata Completeness** - Checks required fields populated
8. **Summary File Validation** - Verifies processing statistics
9. **Log Files Exist** - Confirms pipeline logs created

## Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all integration tests
python development/tests/test_integration.py
```

## Expected Output

```
[INFO] Starting Luminate AI Integration Tests
[INFO] Course ID: _11378_1
[PASS] ✓ Data Directory Exists
[PASS] ✓ JSON Files Count - 593 files found
[PASS] ✓ Course ID Correctness - All sampled files correct
[PASS] ✓ URL Format Validation - All sampled URLs valid
[PASS] ✓ Chunk Structure Validation - All chunks valid
[PASS] ✓ Graph Relationships - 1296 links with valid structure
[PASS] ✓ Metadata Completeness - All metadata valid
[PASS] ✓ Summary File Validation - Summary accurate
[PASS] ✓ Log Files Exist - All logs present
[INFO] Test Summary
[INFO] Total: 9, Passed: 9, Failed: 0
[PASS] All integration tests passed!
```

## Test Logs

Test execution logs are saved to `logs/` with timestamps:
- `logs/integration_test_YYYYMMDD_HHMMSS.log`

## Adding New Tests

1. Add test method to `LuminateIntegrationTests` class
2. Name method starting with `test_`
3. Use logger methods: `test_start()`, `test_pass()`, `test_fail()`
4. Add test to `run_all_tests()` method
5. Run test suite to validate

## When to Run

- **Before Phase 3**: Validate Phase 2 data pipeline ✅
- **Before Phase 4**: Add ChromaDB validation tests
- **Before Phase 5**: Add LangGraph agent tests
- **After Major Changes**: Catch regressions
- **CI/CD Pipeline**: Automated validation

## Success Criteria

All 9 tests must pass before proceeding to next phase.
