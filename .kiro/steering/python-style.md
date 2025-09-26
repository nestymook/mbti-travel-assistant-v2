# Python Code Style Guidelines

## PEP8 Compliance

All Python code in this project must strictly adhere to PEP8 (Python Enhancement Proposal 8) style guidelines. This ensures consistent, readable, and maintainable code across the entire codebase.

**Official Reference**: https://peps.python.org/pep-0008/

## Overriding Principle

As stated in PEP8: "A Foolish Consistency is the Hobgoblin of Little Minds"

Code is read much more often than it is written. While consistency with this style guide is important, know when to be inconsistent. Sometimes style guide recommendations just aren't applicable. When in doubt, use your best judgment.

**Good reasons to ignore a particular guideline:**
1. When applying the guideline would make the code less readable
2. To be consistent with surrounding code that also breaks it (for historic reasons)
3. Because the code predates the introduction of the guideline
4. When the code needs to remain compatible with older Python versions

**Consistency hierarchy (most to least important):**
1. Consistency within one module or function
2. Consistency within a project  
3. Consistency with this style guide

## Key PEP8 Requirements

### Indentation
- Use 4 spaces per indentation level
- Never mix tabs and spaces
- Continuation lines should align wrapped elements vertically

### Line Length
- Limit all lines to a maximum of 79 characters
- For docstrings or comments, limit to 72 characters
- Teams may agree to increase line length up to 99 characters (comments/docstrings still at 72)
- Use Python's implicit line continuation inside parentheses, brackets, and braces
- Prefer parentheses over backslashes for line continuation
- Break long lines appropriately to maintain readability

### Imports
- Import statements should be on separate lines
- Group imports in this order:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library specific imports
- Use absolute imports when possible
- Avoid wildcard imports (`from module import *`)

### Naming Conventions
- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES`
- **Private attributes**: prefix with single underscore `_private_var`
- **Internal use**: prefix with double underscore `__internal_var`

### Whitespace
- Avoid extraneous whitespace in expressions and statements
- Use spaces around operators and after commas
- No spaces inside parentheses, brackets, or braces
- No trailing whitespace

### Blank Lines
- Surround top-level function and class definitions with two blank lines
- Method definitions inside a class are surrounded by a single blank line
- Use blank lines in functions sparingly to indicate logical sections
- Extra blank lines may be used sparingly to separate groups of related functions

### Binary Operators
- Break before binary operators (Knuth's style) for better readability:
```python
# Correct:
income = (gross_wages
          + taxable_interest
          + (dividends - qualified_dividends)
          - ira_deduction
          - student_loan_interest)
```

### Tabs or Spaces
- Spaces are the preferred indentation method
- Never mix tabs and spaces
- Use tabs only to remain consistent with existing tab-indented code

### Comments and Docstrings
- Use docstrings for all public modules, functions, classes, and methods
- Follow Google or NumPy docstring conventions
- Keep comments up-to-date with code changes
- Use inline comments sparingly and only when necessary

## Enforcement Tools

### Required Tools
- **flake8**: Primary linting tool for PEP8 compliance
- **black**: Code formatter for automatic PEP8 formatting
- **isort**: Import statement organizer

### Configuration
Add these tools to your development workflow:

```bash
# Install tools
pip install flake8 black isort

# Check compliance
flake8 .

# Auto-format code
black .

# Sort imports
isort .
```

### Pre-commit Integration
Consider using pre-commit hooks to automatically check PEP8 compliance before commits.

## Exceptions and Special Cases
- Line length may exceed 79 characters for:
  - Long URLs in comments
  - Long import statements that cannot be reasonably broken
  - String literals that would be less readable if broken
- Continuation lines may use different indentation than 4 spaces when appropriate
- Break backwards compatibility rules only when absolutely necessary
- Prioritize readability over strict rule adherence when there's a clear benefit

## Examples

### Good PEP8 Style
```python
import os
import sys
from typing import List, Dict

import boto3
import pandas as pd

from services.restaurant_service import RestaurantService


class RestaurantSearchAgent:
    """Agent for searching restaurants using MCP protocol."""
    
    def __init__(self, config_path: str) -> None:
        """Initialize the restaurant search agent.
        
        Args:
            config_path: Path to configuration file.
        """
        self.config_path = config_path
        self._service = RestaurantService()
    
    def search_restaurants(self, query: str, district: str = None) -> List[Dict]:
        """Search for restaurants based on query and optional district.
        
        Args:
            query: Search query string.
            district: Optional district filter.
            
        Returns:
            List of restaurant dictionaries.
        """
        results = self._service.search(query, district)
        return self._format_results(results)
```

### Bad Style (Avoid)
```python
import os,sys
import boto3,pandas as pd
from services.restaurant_service import *

class restaurantSearchAgent:
    def __init__(self,config_path):
        self.config_path=config_path
        self._service=RestaurantService( )
    
    def search_restaurants(self,query,district=None):
        results=self._service.search(query,district)
        return self._format_results( results )
```

## Integration with AgentCore

When developing AgentCore agents and MCP tools, ensure all Python code follows these guidelines to maintain consistency with the broader AWS ecosystem and Python community standards.