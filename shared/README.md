# Apollonia Shared

Shared utilities and models for Apollonia microservices.

## Overview

This package contains common code shared across all Apollonia services:

- **models.py**: Data models and structures
- **logging_utils.py**: Centralized logging configuration

## Installation

This package is automatically installed as a dependency when building Apollonia services.

## Usage

```python
from shared.models import FileMetadata
from shared.logging_utils import setup_logging

# Set up logging for your service
logger = setup_logging("my-service")

# Use shared models
metadata = FileMetadata(...)
```
