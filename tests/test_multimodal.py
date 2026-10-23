""" This file tests the analyze_receipt function. 
    This function calls the AI and parses a complex JSON schema, 
    and mock is done for the OllamaModelClient to return a fake JSON string.
"""

from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError
from decimal import Decimal

from src.capabilities.multimodal import analyze_receipt
from src.schemas.responses import ReceiptData
from src.models.model_client import ModelClientError, OllamaConnectionError


# CASE-01:
# Verifying that a valid image and AI response is correctly parsed into a ReceiptData object.
def test_analyze_receipt_successful():
    mock_client = MagicMock()
    mock_client.generate_from_image.return_value = """
    {
        "is_receipt": true,
        "store": "THE BISTRO",
        "date": "2022-03-18",
        "total": 42.07,
        "currency": "USD",
        "items": [
            {"name": "BURGER DELUXE", "price": 14.99, "category": "Restaurant"},
            {"name": "CAESAR SALAD", "price": 9.99, "category": "Restaurant"},
            {"name": "2 x SOFT DRINK @ $2.99", "price": 5.98, "category": "Restaurant"},
            {"name": "CHEESECAKE", "price": 7.99, "category": "Restaurant"}
        ]
    }
    """

    receipt, raw_text = analyze_receipt("dummy_image.jpg", mock_client)

    assert receipt.store == "THE BISTRO"
    assert str(receipt.date) == "2022-03-18"
    assert receipt.total == Decimal("42.07")
    assert len(receipt.items) == 4
    assert receipt.items[0].name == "BURGER DELUXE"

    # case-01 also requires currency, prices, and categories to be extracted.
    assert receipt.currency == "USD"
    assert receipt.items[0].price == Decimal("14.99")
    assert receipt.items[0].category == "Restaurant"

    # Verify the client was called correctly
    mock_client.generate_from_image.assert_called_once()
    call_args = mock_client.generate_from_image.call_args[1]
    assert "Analyze this picture" in call_args["prompt"]
    assert call_args["image_path"] == "dummy_image.jpg"


# CASE-13: Verify that if the AI hallucinates invalid JSON, a Pydantic ValidationError is raised.
def test_analyze_receipt_invalid_ai_json():
    mock_client = MagicMock()
    # Missing required fields (like 'items' or 'total') or malformed JSON
    mock_client.generate_from_image.return_value = '{"store": "THE BISTRO"}'
    
    with pytest.raises(ValidationError):
        analyze_receipt("image.jpg", mock_client)


# CASE-14: Verify that Ollama errors propagate up to the UI layer correctly.
def test_analyze_receipt_handles_model_client_error():
    mock_client = MagicMock()
    mock_client.generate_from_image.side_effect = OllamaConnectionError("Connection refused")
    
    with pytest.raises(OllamaConnectionError):
        analyze_receipt("image.jpg", mock_client)


