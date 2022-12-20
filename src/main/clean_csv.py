import csv
from typing import List

# Map these to required headers --> Date, Cost, Description
# Remove negative sign from field if it exists
# Check if positive sign needs to be in the file
# Create clean csv


class CleanCsv:
    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path

    def extract_headers(self) -> List[str]:
        """
        Extract header values from csv file. User needs to provide input on
        type of delimiter.
        Returns:
            List[str]: header values as a list of string.
        """
        with open(self.file_path) as csv_file:
            dialect = csv.Sniffer().sniff(csv_file.read(1024))
            csv_file.seek(0)
            csv_reader = csv.reader(csv_file, dialect)
            headers: List[str] = next(csv_reader)
            return headers
