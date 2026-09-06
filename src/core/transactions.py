import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class Transaction:
    """
    A single normalized row from a cleaned CSV (see `clean_csv.py`), prior
    to being reviewed and turned into an Expense.
    """

    date: date
    amount: Decimal
    description: str
    currency: str


def parse_transaction_row(row: Dict[str, str]) -> Transaction:
    return Transaction(
        date=datetime.strptime(row["date"], "%d/%m/%Y").date(),
        amount=Decimal(row["amount"]),
        description=row["description"],
        currency=row["currency"],
    )


def read_transactions_csv(path: Path) -> List[Transaction]:
    with open(path, newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        return [parse_transaction_row(row) for row in reader]
