from datetime import date
from decimal import Decimal

from src.core.transactions import parse_transaction_row, read_transactions_csv


def test_parse_transaction_row_parses_date_amount_description_currency():
    transaction = parse_transaction_row(
        {
            "date": "30/12/2023",
            "amount": "38.50",
            "description": "PELE MELE XL Ixelles to:",
            "currency": "EUR",
        }
    )

    assert transaction.date == date(2023, 12, 30)
    assert transaction.amount == Decimal("38.50")
    assert transaction.description == "PELE MELE XL Ixelles to:"
    assert transaction.currency == "EUR"


def test_read_transactions_csv_reads_a_semicolon_delimited_file(tmp_path):
    csv_path = tmp_path / "transactions_clean.csv"
    csv_path.write_text(
        "date;amount;description;currency\n"
        "30/12/2023;38.50;PELE MELE XL Ixelles to:;EUR\n"
        "29/12/2023;47.70;Black and white Docks BRUXELLES to:;EUR\n"
    )

    transactions = read_transactions_csv(csv_path)

    assert len(transactions) == 2
    assert transactions[0].date == date(2023, 12, 30)
    assert transactions[0].amount == Decimal("38.50")
    assert transactions[1].description == "Black and white Docks BRUXELLES to:"
