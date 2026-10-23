"""Integration tests: real Ollama client + real fixture images.

These tests exercise the actual model on hard/failure-case images. They are
marked `integration` so they can be excluded from fast CI runs:

Assertions are intentionally *property-based* (not exact values), because the
model's output varies run-to-run. We assert the field is present / plausible,
not that it equals one specific number.
"""

from pathlib import Path

import pytest
from decimal import Decimal

from src.capabilities.multimodal import analyze_receipt
from src.models.model_client import OllamaModelClient


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def client():
    """Real Ollama client. Requires a running Ollama instance with the
    configured model pulled locally. Shared across all tests in this module
    so we pay the client-construction cost once."""
    return OllamaModelClient()


# Helpers
def _assert_basic_receipt_fields(receipt):
    """Assert the fields that EVERY successful extraction must produce,
    without pinning exact values (model output varies)."""
    assert receipt.is_receipt is True, "Model should identify this as a receipt"
    assert receipt.store, "store must be non-empty"
    assert receipt.total is not None, "total must be present"
    assert receipt.date is not None, "date must be present"
    assert receipt.currency, "currency must be present"
    assert receipt.items, "at least one line item should be extracted"
    for item in receipt.items:
        assert item.name, "every line item needs a name"
        assert item.price is not None, "every line item needs a price"
        assert item.category, "every line item needs a category"



# CASE-06: wrinkled receipt
@pytest.mark.integration
def test_wrinkled_receipt(client):
    """case-06: extract fields from a wrinkled receipt despite the distortion."""
    receipt, raw_text = analyze_receipt(FIXTURES / "wrinkled_receipt.jpg", client)

    _assert_basic_receipt_fields(receipt)
    # Additional soft check: line items got categorised (not left blank).
    assert all(i.category for i in receipt.items)



# CASE-07: blurred receipt
@pytest.mark.integration
def test_blurred_receipt(client):
    """case-07: extract fields from a blurred receipt despite the blur."""
    receipt, raw_text = analyze_receipt(FIXTURES / "blurred_receipt.jpg", client)

    _assert_basic_receipt_fields(receipt)
    assert all(i.category for i in receipt.items)



# CASE-08: long receipt
@pytest.mark.integration
def test_long_receipt(client):
    """case-08: extract fields from a long (multi-item) receipt."""
    receipt, raw_text = analyze_receipt(FIXTURES / "long_receipt.jpg", client)

    _assert_basic_receipt_fields(receipt)
    # A "long" receipt should produce many items — a weak lower bound that
    # doesn't depend on exact count but proves the model didn't truncate.
    assert len(receipt.items) >= 5, (
        f"Long receipt should yield several line items, got {len(receipt.items)}"
    )



# CASE-09: not a receipt
@pytest.mark.integration
def test_not_a_receipt(client):
    """case-09: the model should flag a non-receipt image via is_receipt=False.

    We do NOT assert an exception is raised — the case says the application
    returns the message 'Image is not a receipt.', which the UI produces when
    `receipt.is_receipt is False`. So we assert the flag, not an exception.
    """
    receipt, raw_text = analyze_receipt(FIXTURES / "not_a_receipt.jpg", client)

    assert receipt.is_receipt is False, (
        "Non-receipt image should be flagged with is_receipt=False"
    )


# CASE-12: custom user instruction overrides categories
@pytest.mark.integration
def test_custom_instruction_overrides_categories(client):
    """case-12: when instructed to categorise everything as 'Household',
    the model should override its default categorisation."""
    receipt, raw_text = analyze_receipt(
        FIXTURES / "normal_receipt.jpg",
        client,
        user_instructions="Categorize all the items as Household.",
    )

    assert receipt.is_receipt is True
    assert receipt.items, "receipt should still have line items"
    non_household = [
        (i.name, i.category) for i in receipt.items if i.category != "Household"
    ]
    assert not non_household, (
        f"All items should be categorised as 'Household', but these were not: "
        f"{non_household}"
    )

# CASE-13: Upload a image of receipt which is missing metadata
# missing metadata (date)
# extract fields from a receipt that has no date. The model should set date=None and NOT hallucinate a date.
@pytest.mark.integration
def test_receipt_missing_date(client):
    receipt, raw_text = analyze_receipt(FIXTURES / "no_date_receipt.jpg", client)

    _assert_basic_receipt_fields(receipt)
    assert receipt.date is None, (
        f"Model hallucinated a date ({receipt.date}) on a receipt that has none."
    )
    # Based on your colleague's manual test, the total was 27.35
    assert receipt.total == Decimal("27.35")



# CASE-14: Extremely blurred or barely readable image of a receipt
# extremely blurred receipt should fail gracefully (not crash)
@pytest.mark.integration
def test_extremely_blurred_receipt(client):

    from pydantic import ValidationError
    
    # We expect the model to hallucinate or output invalid JSON on a 
    # heavy blur. If it magically succeeds, that's fine too, but it should 
    # NOT crash with a random Python error.
    try:
        receipt, raw_text = analyze_receipt(FIXTURES / "extremely_blurred_receipt.jpg", client)
        # If it did parse, it should at least be a valid ReceiptData object
        assert receipt.is_receipt is True or receipt.is_receipt is False
    except ValidationError:
        # This is the expected path: the model failed, Pydantic caught it.
        pass
    except Exception as e:
        pytest.fail(f"analyze_receipt crashed with an unexpected error: {type(e).__name__}: {e}")



# CASE-15: Uploading an image of a receipt and giving user instructions 'Currency is EUR'.
# custom user instruction overrides currency

@pytest.mark.integration
def test_custom_instruction_overrides_currency(client):
    """case-15: instruct the model to use EUR. It should extract the items
    as-is but change the currency to EUR (even though the receipt is in USD)."""
    receipt, raw_text = analyze_receipt(
        FIXTURES / "harbor_lane_cafe.jpg",
        client,
        user_instructions="Currency is EUR",
    )

    assert receipt.is_receipt is True
    # The original receipt is from Chicago, IL and uses $ (USD)
    # But the user instruction should override it to EUR
    assert receipt.currency == "EUR", f"Expected EUR, but got {receipt.currency}"
    
    # Verify it still extracted the other data correctly
    assert receipt.store == "HARBOR LANE CAFE" or "HARBOR LANE" in receipt.store
    assert receipt.total == Decimal("31.39")
    assert str(receipt.date) == "2019-11-20"