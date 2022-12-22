import sys

from src.main.clean_csv import CleanCsv

if __name__ == "__main__":
    file_path = sys.argv[1]
    clean_csv_file = CleanCsv(file_path)
    clean_csv_file.run_pipeline()
