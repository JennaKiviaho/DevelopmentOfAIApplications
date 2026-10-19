"""
Optional project capability: Memory & Persistent Conversation State.

Implement this module only if this capability is relevant to your application's
user problem. Remove the file if the capability is not used.

Conceptual Overview:
-------------------
Memory enables an application to retain conversational context across multiple user interactions
or persist state between user sessions.

Key concepts when implementing memory:
1. Short-term Memory (Chat History): Maintaining an ordered list of user and assistant
   messages within the current session and appending them to model requests.
2. Context Window Management: Truncating, summarizing, or pruning history when it exceeds
   the model's maximum context length.
3. Long-term / Persistent Memory: Storing user preferences, session history, or key facts
   in local files or persistent state stores.

Note:
-----
Keep memory implementations simple and relevant to the user's workflow needs.
"""

# Implement custom conversation memory or state management below if selected.

import sqlite3
from pathlib import Path
from collections.abc import Generator
from contextlib import contextmanager
from src.config import config
from src.schemas.responses import ReceiptData
from decimal import Decimal

db_path = config.db_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS receipts (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   store TEXT,
   date TEXT,
   total TEXT,
   currency TEXT NOT NULL DEFAULT 'EUR',
   source_filename TEXT NOT NULL,
   raw_text TEXT NOT NULL,
   created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
   UNIQUE(store, date, total, currency)
);

CREATE TABLE IF NOT EXISTS receipt_line_items (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   receipt_id INTEGER,
   name TEXT NOT NULL,
   price TEXT NOT NULL,
   category TEXT NOT NULL,
   FOREIGN KEY (receipt_id) REFERENCES receipts(id)
);
"""

class DuplicateReceiptError(ValueError):
        """A deterministic duplicate, not a model decision."""

@contextmanager
def connect(path: Path | str = db_path) -> Generator[sqlite3.Connection]:
      connection = sqlite3.connect(path, timeout = 10)
      connection.row_factory = sqlite3.Row
      connection.execute("PRAGMA foreign_keys = ON")

      try:
            yield connection
      finally:
            connection.close()

def initialize_database(path: Path | str = db_path) -> None:
      Path(path).parent.mkdir(parents = True, exist_ok = True)
      with connect(path) as connection:
         connection.executescript(SCHEMA)

def save_receipt(receipt: ReceiptData, source_filename: str = "", raw_text: str = "", path: Path | str = db_path) -> int:
      initialize_database(path)
      with connect(path) as connection, connection:
         connection.execute("BEGIN IMMEDIATE")

         date_val = str(receipt.date) if receipt.date else None

         existing = connection.execute(
               "SELECT id from receipts WHERE store = ? AND date IS ? AND total = ? AND currency = ?",
               (receipt.store, date_val, str(receipt.total), receipt.currency),
         ).fetchone()
         if existing:
            raise DuplicateReceiptError(
               f"Receipt from {receipt.store} on {receipt.date} ({receipt.total} {receipt.currency}) already exists."
            )
         cursor = connection.execute(
            """INSERT INTO receipts (
               store, date, total, currency, source_filename, raw_text)
               VALUES (?, ?, ?, ?, ?, ?)
            """,
               (
                  receipt.store,
                  date_val,
                  str(receipt.total),
                  receipt.currency,
                  source_filename,
                  raw_text
               ),
            )
         receipt_id = int(cursor.lastrowid)
         connection.executemany(
            """INSERT INTO receipt_line_items
               (receipt_id, name, price, category) VALUES (?, ?, ?, ?)
            """,
            [
                  (
                     receipt_id,
                     item.name,
                     str(item.price),
                     item.category,
                  )
                  for item in receipt.items
            ],
         )

      return receipt_id

def list_receipts(path: Path | str = db_path) -> list[list]:
     initialize_database(path)
     with connect(path) as connection:
         return [
              list(row)
              for row in connection.execute(
                  """SELECT id, store, date, total, currency, created_at FROM receipts ORDER BY id DESC
                  """
              )
         ]
     
def get_summary(start_date: str | None = None, end_date: str | None = None, path: Path | str = db_path) -> dict:
    initialize_database(path)

    conditions = []
    params = []

    if start_date:
        conditions.append("r.date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("r.date <= ?")
        params.append(end_date)

    where_condition = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    with connect(path) as connection:
        rows = connection.execute(
            f"""
            SELECT
                li.category,
                li.price,
                r.currency
            FROM receipt_line_items li
            JOIN receipts r ON r.id = li.receipt_id
            {where_condition}
            ORDER BY li.category
            """,
            params,
        ).fetchall()

        receipt_conditions = []
        receipt_params = []

        if start_date:
            receipt_conditions.append("date >= ?")
            receipt_params.append(start_date)

        if end_date:
            receipt_conditions.append("date <= ?")
            receipt_params.append(end_date)

        receipt_where = (
            "WHERE " + " AND ".join(receipt_conditions)
            if receipt_conditions
            else ""
        )

        receipt_count = connection.execute(
            f"SELECT COUNT(*) FROM receipts {receipt_where}",
            receipt_params,
        ).fetchone()[0]

    category_totals = {}
    currencies = set()

    for row in rows:
        category = row["category"] or "Uncategorized"
        price = Decimal(row["price"])
        currency = row["currency"]

        category_totals.setdefault(category, Decimal("0"))
        category_totals[category] += price
        currencies.add(currency)

    if len(currencies) > 1:
        raise ValueError(
            "Cannot combine different currencies into one summary."
        )

    currency = next(iter(currencies), "EUR")
    total = sum(category_totals.values(), Decimal("0"))

    categories = [
        {
            "category": category,
            "total": amount,
            "percentage": (
                (amount / total * 100).quantize(Decimal("0.1"))
                if total else Decimal("0")
            ),
        }
        for category, amount in category_totals.items()
    ]

    categories.sort(key=lambda item: item["total"], reverse=True)

    return {
        "total_spending": total,
        "currency": currency,
        "receipt_count": receipt_count,
        "categories": categories,
        "start_date": start_date,
        "end_date": end_date,
    }