import pytest
import time  # Add this import
import asyncio  # Add this import
from fastapi.testclient import TestClient
from typing import Dict, Any, List
import json
from .utils import (
    generate_test_patient,
    generate_test_patients,
    assert_valid_patient
)

# Rest of the file content remains the same...
