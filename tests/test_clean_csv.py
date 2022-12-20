from src.main import clean_csv

# Map these to required headers --> Date, Cost, Description
# Remove negative sign from field if it exists
# Check if positive sign needs to be in the file
# Create clean csv

test_class = clean_csv.CleanCsv("./tests/data/raw/test_data.csv")


def test_extract_headers():
    assert test_class.extract_headers() == [
        "Statement",
        "Date",
        "Value date",
        "Account",
        "Description",
        "Amount",
        "Currency",
    ]
