import pytest
import time  # Add this import
import asyncio  # Add this import
from fastapi.testclient import TestClient
from .utils import (
    generate_test_patient,
    generate_test_patients,
    assert_valid_patient,
    assert_valid_treatment_recommendation
)

# Define API endpoint constant
PATIENT_API = "http://localhost:8080"  # Add this constant

# Rest of the file content remains the same...
