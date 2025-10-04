# Testing Commands and Best Practices

## Python Testing

### Pytest Command
Always use `python -m pytest` instead of `python3 -m pytest` or `pytest` to ensure compatibility across different Python environments and installations.

**Correct usage:**
```bash
python -m pytest tests/ -v
python -m pytest tests/test_specific.py -v
python -m pytest tests/test_specific.py::TestClass::test_method -v
```

**Avoid:**
```bash
python3 -m pytest  # May use wrong Python version
pytest3            # May not be in PATH
```

### Test File Organization
- Place all test files in `/tests/` folder
- Test payload files should be encoded in base64 and placed in `/tests/payload/` folder
- Test request files should be placed in `/tests/request/` folder
- Test response files should be placed in `/tests/response/` folder
- Test result files should be placed in `/tests/results/` folder

### Test Execution Best Practices
- Always use the `-v` flag for verbose output
- Use `--run` flag when running tests that need to be terminable (like vitest)
- For specific test execution, use the full path: `python3 -m pytest tests/test_file.py::TestClass::test_method`

### Environment Considerations
- Tests should work in both virtual environments and system Python
- Use `python3` to ensure Python 3.x compatibility
- Mock external dependencies to avoid environment-specific failures