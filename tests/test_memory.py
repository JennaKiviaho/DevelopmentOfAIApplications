""" This file tests SQLite database and functionalities.
    tmp_path (a built-in pytest feature) is used to create a temporary database file in order not to mess up real data.
"""

import pytest
from decimal import Decimal
from src.capabilities.memory import (
    initialize_database, 
    save_receipt, 
    list_receipts, 
    get_summary,
    DuplicateReceiptError
)
from src.schemas.responses import ReceiptData, ReceiptLineItem


@pytest.fixture
# temp db file for testing
def temp_db(tmp_path):
    return tmp_path / "test_receipts.db"


@pytest.fixture
def sample_receipt():
    # Sample receipt data for testing
    return ReceiptData(
        is_receipt=True,
        store="THE BISTRO",
        date="2022-03-18",
        total=42.07,
        currency="USD",
        items=[
            ReceiptLineItem(name="BURGER", price=14.99, category="Restaurant"),
            ReceiptLineItem(name="SALAD", price=9.99, category="Restaurant")
        ]
    )

# Verifying the database and tables are created ok
def test_initialize_database_creates_tables(temp_db):
    initialize_database(temp_db)
    assert temp_db.exists()

# Verifying receipt can be saved and retrieved. App needs to be able to save and retrieve receipts from the database.
def test_save_and_list_receipts(temp_db, sample_receipt):
    receipt_id = save_receipt(sample_receipt, source_filename="bistro.jpg", path=temp_db)
    assert receipt_id == 1

    receipts = list_receipts(path=temp_db)
    assert len(receipts) == 1
    assert receipts[0][1] == "THE BISTRO"
    assert receipts[0][3] == "42.07"
    assert receipts[0][4] == "USD"


# Verify that saving the exact same receipt twice raises DuplicateReceiptError. This for protecting against duplicate bill uploads in the database.
def test_prevent_duplicate_receipts(temp_db, sample_receipt):
    save_receipt(sample_receipt, path=temp_db)
    
    with pytest.raises(DuplicateReceiptError):
        # Try to save the exact same receipt again
        save_receipt(sample_receipt, path=temp_db)


def test_get_summary_calculates_correctly(temp_db, sample_receipt):
    save_receipt(sample_receipt, path=temp_db)
    
    summary = get_summary(path=temp_db)
    
    assert "currencies" in summary
    assert len(summary["currencies"]) == 1
    
    # Get the USD data from the list
    usd_summary = summary["currencies"][0]
    
    assert usd_summary["currency"] == "USD"
    assert usd_summary["receipt_count"] == 1
    
    assert usd_summary["total_spending"] == Decimal("42.07") 
    
    # Check categories
    assert len(usd_summary["categories"]) == 1
    assert usd_summary["categories"][0]["category"] == "Restaurant"
    assert usd_summary["categories"][0]["total"] == Decimal("24.98")
    assert usd_summary["categories"][0]["percentage"] == Decimal("59.4")
