# Migration Guide: Upgrading from retry-scraper to HoneyGraber

## Overview

We've renamed the library from `retry-scraper` to `HoneyGraber` to avoid conflicts with Python's standard retry modules. This guide will help you migrate your existing code to use the new package.

## Installation Changes

1. Uninstall the old package:
   ```bash
   pip uninstall retry-scraper
   ```

2. Install the new package:
   ```bash
   pip install honeygraber
   ```

## Import Changes

Update your imports from:

```python
from retry import RetrySC, Rule, Rules  # Old imports
```

To:

```python
from honeygraber import RetrySC, Rule, Rules  # New imports
```

### Detailed Import Changes

| Old Import | New Import |
|------------|------------|
| `from retry import RetrySC` | `from honeygraber import RetrySC` |
| `from retry.utils.pagination import PaginationHandler` | `from honeygraber.utils.pagination import PaginationHandler` |
| `from retry.utils.cache import SimpleCache` | `from honeygraber.utils.cache import SimpleCache` |
| `from retry.nlp import EntityExtractor` | `from honeygraber.nlp import EntityExtractor` |

## API Compatibility

The good news is that the API remains exactly the same. We've maintained backward compatibility with the class and method names, so your existing code should work after updating the imports.

## Why the Change?

The original name `retry` was causing confusion with the Python standard retry modules and other retry-related packages. The new name `HoneyGraber` better represents the library's purpose (like a honey badger tenaciously grabbing data) and avoids namespace conflicts.

## Features and Improvements

Along with the name change, version 0.2.0 includes:

- Improved error handling with custom exceptions
- Enhanced NLP capabilities
- Better proxy management and rate limiting
- More flexible caching options
- Support for various authentication methods
- More comprehensive documentation

## Need Help?

If you encounter any issues during migration, please:

1. Check the [GitHub repository](https://github.com/yonatan-levin/honeygraber)
2. Open an issue if needed
3. Refer to the updated documentation and examples

We appreciate your patience and support during this transition! 