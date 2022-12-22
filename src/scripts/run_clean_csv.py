import argparse
from pathlib import Path

from src.main.clean_csv import CleanCsv

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")
    args = parser.parse_args()
    file_path = Path(args.file_path)

    if file_path.exists():
        clean_csv_file = CleanCsv(file_path)
        clean_csv_file.run_pipeline()
    else:
        print(
            (
                "The given filepath is incorrect. Please check if this "
                f"filepath exists - {file_path}"
            )
        )
