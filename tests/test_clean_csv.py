from typing import Dict, List

from src.main import clean_csv

test_class = clean_csv.CleanCsv("./tests/data/raw/test_data_raw.csv")
raw_headers: List[str] = [
    "Statement",
    "Date",
    "Value date",
    "Account",
    "Description",
    "Amount",
    "Currency",
]

mapped_headers: Dict[str, str] = {
    "date": "Date",
    "amount": "Amount",
    "description": "Description",
    "currency": "Currency",
}


def test_map_headers():
    assert test_class.map_headers(raw_headers) == mapped_headers


# def test_clean_amount_values():
#     assert test_class.clean_amount_values
