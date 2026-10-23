""" This file tests SQLite database and functionalities.
    tmp_path (a built-in pytest feature) is used to create a temporary database file in order not to mess up real data.
"""

import pytest
import sqlite3
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
    # Sample receipt data for testing (USD)
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


@pytest.fixture
def sample_receipt_eur():
    # Second receipt in a different currency, distinct content so it isn't a duplicate
    return ReceiptData(
        is_receipt=True,
        store="CAFE MILANO",
        date="2022-03-20",
        total=18.50,
        currency="EUR",
        items=[
            ReceiptLineItem(name="ESPRESSO", price=3.50, category="Restaurant"),
            ReceiptLineItem(name="PASTA", price=15.00, category="Restaurant"),
        ],
    )


# Verifying the database and tables are created ok
def test_initialize_database_creates_tables(temp_db):
    initialize_database(temp_db)
    assert temp_db.exists()



# CASE-02 / CASE-03 (combined smoke test): The application must be able to save
# a receipt and then list it back out.
# Verifying receipt can be saved and retrieved. App needs to be able to save and retrieve receipts from the database.
def test_save_and_list_receipts(temp_db, sample_receipt):
    receipt_id = save_receipt(sample_receipt, source_filename="bistro.jpg", path=temp_db)
    assert receipt_id == 1

    receipts = list_receipts(path=temp_db)
    assert len(receipts) == 1
    assert receipts[0][1] == "THE BISTRO"
    assert receipts[0][3] == "42.07"
    assert receipts[0][4] == "USD"


# CASE-02: receipt AND its line items are saved in the database.
def test_save_receipt_persists_line_items(temp_db, sample_receipt):
    save_receipt(sample_receipt, source_filename="bistro.jpg", path=temp_db)

    conn = sqlite3.connect(temp_db)
    try:
        rows = conn.execute(
            "SELECT name, price, category FROM receipt_line_items ORDER BY name"
        ).fetchall()
    finally:
        conn.close()

    assert rows == [
        ("BURGER", "14.99", "Restaurant"),
        ("SALAD", "9.99", "Restaurant"),
    ]


# CASE-03: My Receipts listing shows store, date, total and currency.

def test_list_receipts_includes_date(temp_db, sample_receipt):
    save_receipt(sample_receipt, path=temp_db)
    receipts = list_receipts(path=temp_db)

    assert len(receipts) == 1
    # Column order matches test_save_and_list_receipts: id, store, date, total, currency
    assert receipts[0][2] == "2022-03-18"



# CASE-04: Save three different receipts, refresh, all three appear.

def test_list_receipts_returns_all_saved(temp_db):
    receipts_to_save = [
        ReceiptData(
            is_receipt=True, store="STORE A", date="2022-03-01", total=10.00,
            currency="USD",
            items=[ReceiptLineItem(name="ITEM A", price=10.00, category="Food")],
        ),
        ReceiptData(
            is_receipt=True, store="STORE B", date="2022-03-02", total=20.00,
            currency="USD",
            items=[ReceiptLineItem(name="ITEM B", price=20.00, category="Food")],
        ),
        ReceiptData(
            is_receipt=True, store="STORE C", date="2022-03-03", total=30.00,
            currency="USD",
            items=[ReceiptLineItem(name="ITEM C", price=30.00, category="Food")],
        ),
    ]
    for r in receipts_to_save:
        save_receipt(r, path=temp_db)

    # "Refresh Receipts" in the UI is just another list_receipts call.
    listed = list_receipts(path=temp_db)
    assert len(listed) == 3
    assert {row[1] for row in listed} == {"STORE A", "STORE B", "STORE C"}


# CASE-05: Spending Summary — totals and counts grouped by currency.

# Single-currency summary: totals, counts, and category breakdown.
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


# Multi-currency summary: grouping across USD and EUR.
def test_get_summary_groups_multiple_currencies(temp_db, sample_receipt, sample_receipt_eur):
    save_receipt(sample_receipt, path=temp_db)      # USD 42.07
    save_receipt(sample_receipt_eur, path=temp_db)  # EUR 18.50

    summary = get_summary(path=temp_db)

    by_currency = {c["currency"]: c for c in summary["currencies"]}
    assert set(by_currency) == {"USD", "EUR"}

    assert by_currency["USD"]["receipt_count"] == 1
    assert by_currency["USD"]["total_spending"] == Decimal("42.07")

    assert by_currency["EUR"]["receipt_count"] == 1
    assert by_currency["EUR"]["total_spending"] == Decimal("18.50")


# CASE-11: Verify that saving the exact same receipt twice raises DuplicateReceiptError.
# Duplicete protection 
def test_prevent_duplicate_receipts(temp_db, sample_receipt):
    save_receipt(sample_receipt, path=temp_db)

    with pytest.raises(DuplicateReceiptError):
        # Try to save the exact same receipt again
        save_receipt(sample_receipt, path=temp_db)