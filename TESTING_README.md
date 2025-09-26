# FWMIS Automated Testing Suite

This directory contains a comprehensive automated testing suite for the Financial Write-off Management Information System (FWMIS). The suite provides end-to-end testing coverage for all major functionality including case import, workflow processing, and duplicate prevention.

## 🎯 Quick Start

### Run All Tests
```bash
python test_runner.py
```

### Run Specific Test Categories
```bash
# Import tests only
python test_runner.py --import-only

# Workflow tests only
python test_runner.py --workflow-only

# Quick tests (skip slow ones)
python test_runner.py --quick
```

### Generate Test Data
```bash
# Generate 100 test cases in database
python test_data_generator.py --cases 100

# Generate 5 BAS files
python test_data_generator.py --bas-files 5

# Generate dummy PDF evidence files
python test_data_generator.py --evidence 10
```

## 📋 Test Categories

### 1. Import Tests (`TestCaseImport`)
- **BAS Parser Testing**: Validates BAS file parsing functionality
- **Import Dialog Creation**: Tests UI component initialization
- **Duplicate Detection**: Ensures import process prevents duplicates

### 2. Workflow Tests (`TestFWMISWorkflow`)
- **Case Creation**: Tests initial case creation with correct status
- **Status Transitions**: Validates workflow state changes
- **Full Workflow**: End-to-end case processing from import to completion
- **Search & Filtering**: Tests case search and filtering capabilities

### 3. Duplicate Prevention (`TestDuplicatePrevention`)
- **Transaction Uniqueness**: Database-level duplicate prevention
- **Import Duplicate Detection**: Logic-level duplicate checking

### 4. Performance Tests (`TestPerformance`)
- **Bulk Operations**: Tests creating multiple cases efficiently
- **Query Performance**: Validates database query speed
- **Memory Usage**: Monitors resource consumption

## 🛠️ Test Files

| File | Purpose |
|------|---------|
| `test_automated_suite.py` | Main test suite with all test cases |
| `test_runner.py` | Command-line test runner with environment setup |
| `test_data_generator.py` | Generates test data (cases, BAS files, PDFs) |
| `.github/workflows/test_automation.yml` | CI/CD pipeline configuration |

## 🔧 Manual Testing vs Automated Testing

### What Manual Testing Covers Well
- User interface validation
- Visual feedback verification
- Usability testing
- Exploratory testing

### What Automated Testing Covers Better
- **Regression Testing**: Catch bugs introduced by code changes
- **Workflow Validation**: Ensure business logic remains intact
- **Performance Monitoring**: Detect performance degradation
- **Data Integrity**: Validate database constraints and relationships
- **Edge Cases**: Test scenarios that are difficult to reproduce manually

## 🚀 Running Tests in Different Environments

### Local Development
```bash
# Full test suite
python test_runner.py

# With pytest directly
python -m pytest test_automated_suite.py -v
```

### CI/CD Pipeline
The GitHub Actions workflow (`.github/workflows/test_automation.yml`) runs:
- Unit tests on every push/PR
- Integration tests on successful unit tests
- Performance tests on successful integration tests
- Daily scheduled runs for regression testing

### Test Database Isolation
- Tests use a separate database (`fwmis_test.db`) to avoid affecting production data
- Original database is backed up and restored after testing
- Environment variables control test mode behavior

## 📊 Test Data Management

### Sample BAS Files
Located in `data/` directory:
- `Int_pd_other_partial.TXT` - Partial transaction set
- `Int_pd_other_complete.TXT` - Complete transaction set
- `Int_pd_municipalities.TXT` - Municipal transactions

### Test Database
- Test cases are created with transaction numbers prefixed with test identifiers
- Financial year `2025-2026` is used for all test data
- Cases are distributed across different lists and statuses

### Evidence Files
- Dummy PDF files are generated for evidence attachment testing
- Located in `data/test_data/` directory

## 🐛 Debugging Failed Tests

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database path
   python -c "from scripts.Utilities.config import DB_PATH; print(DB_PATH)"
   ```

2. **Import Path Issues**
   ```bash
   # Verify Python path
   python -c "import sys; print('\\n'.join(sys.path))"
   ```

3. **Qt/GUI Testing Issues**
   - Some tests may fail in headless environments
   - Use `pytest --tb=long` for detailed error traces

### Running Tests with Debug Output
```bash
# Verbose output
python -m pytest test_automated_suite.py -v -s

# Stop on first failure
python -m pytest test_automated_suite.py -x

# Run specific test
python -m pytest test_automated_suite.py::TestFWMISWorkflow::test_full_case_workflow -v
```

## 📈 Performance Testing

### Benchmarking
```bash
# Run performance benchmarks
python -m pytest test_automated_suite.py::TestPerformance --benchmark-only

# Save benchmark results
python -m pytest test_automated_suite.py::TestPerformance --benchmark-json=perf_results.json
```

### Performance Metrics Tracked
- Case creation speed (cases/second)
- Query response times
- Memory usage during bulk operations
- Database transaction performance

## 🔄 CI/CD Integration

### Automated Triggers
- **Push to main/develop**: Full test suite
- **Pull Requests**: Full test suite + integration tests
- **Daily Schedule**: Regression testing

### Test Results
- Test reports are generated as HTML
- Performance benchmarks are tracked over time
- Failed tests block deployments

## 🛡️ Test Safety Features

### Database Protection
- Production database is never modified
- Automatic backup and restore
- Test database isolation

### Resource Management
- Temporary files are cleaned up
- Database connections are properly closed
- Memory usage is monitored

### Error Handling
- Tests fail gracefully with detailed error messages
- Cleanup runs even if tests fail
- No leftover test data in production

## 🎯 Extending the Test Suite

### Adding New Tests
1. Add test methods to appropriate test classes
2. Use descriptive test names: `test_should_do_something`
3. Include docstrings explaining test purpose
4. Use fixtures for common setup/teardown

### Adding Test Data
1. Use `test_data_generator.py` for new data types
2. Update sample data pools in the generator
3. Ensure test data doesn't conflict with production data

### Performance Testing
1. Add benchmark decorators to performance-critical functions
2. Compare results against baseline metrics
3. Monitor for performance regressions

## 📞 Support

If tests are failing or you need help:

1. Check the test output for error details
2. Run individual tests to isolate issues
3. Verify test environment setup
4. Check database connectivity
5. Review recent code changes that might affect tests

## 🔄 Maintenance

### Regular Tasks
- Update test data when schema changes
- Review and update performance baselines
- Clean up obsolete test files
- Update CI/CD configuration for new requirements

### Version Compatibility
- Tests are designed to work with current dependencies
- Update `requirements_optimized.txt` if new testing dependencies are needed
- Ensure backward compatibility with existing test data
