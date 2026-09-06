import csv
import os
import re

import pandas as pd


class ExtractWiseTransactions:
    def __init__(self, file_path: str) -> None:
        self.file_path: str = str(file_path)

    def run_pipeline(self) -> None:

        print("Extracting Wise transactions.\n")

        raw_df: pd.DataFrame = self.read_csv_file()

        filtered_df: pd.DataFrame = self.filter_transactions(raw_df)

        extracted_df: pd.DataFrame = self.extract_columns(filtered_df)

        clean_df: pd.DataFrame = self.format_values(extracted_df)

        self.write_output_file(clean_df)

    def read_csv_file(self) -> pd.DataFrame:
        """
        Detect the delimiter and read the raw Wise transactions csv file.

        Returns:
            pd.DataFrame: raw dataframe.
        """
        with open(self.file_path) as csv_file:
            dialect = csv.Sniffer().sniff(csv_file.read(1024))

        return pd.read_csv(self.file_path, sep=dialect.delimiter)

    def filter_transactions(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Keep only completed, outgoing card transactions - i.e. discard
        transfers, balance cashback and refunded transactions.

        Args:
            raw_df (pd.DataFrame): raw dataframe.

        Returns:
            pd.DataFrame: filtered dataframe.
        """
        filtered_df: pd.DataFrame = raw_df[
            (raw_df["Direction"] == "OUT")
            & (raw_df["Status"] == "COMPLETED")
            & (raw_df["ID"].str.startswith("CARD_TRANSACTION"))
        ].reset_index(drop=True)

        return filtered_df

    def extract_columns(self, filtered_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract the 'Created on', 'Source fee currency',
        'Source amount (after fees)' and 'Target name' columns.

        Args:
            filtered_df (pd.DataFrame): filtered dataframe.

        Returns:
            pd.DataFrame: dataframe with only the required columns.
        """
        return filtered_df[
            [
                "Created on",
                "Source fee currency",
                "Source amount (after fees)",
                "Target name",
            ]
        ].copy()

    def format_values(self, extracted_df: pd.DataFrame) -> pd.DataFrame:
        """
        Format 'Created on' as DD/MM/YYYY and negate 'Source amount (after
        fees)' with a comma decimal separator.

        Args:
            extracted_df (pd.DataFrame): dataframe with only the required
            columns.

        Returns:
            pd.DataFrame: dataframe with formatted values.
        """
        clean_df: pd.DataFrame = extracted_df.copy()

        clean_df["Created on"] = pd.to_datetime(
            clean_df["Created on"]
        ).dt.strftime("%d/%m/%Y")

        clean_df["Source amount (after fees)"] = clean_df[
            "Source amount (after fees)"
        ].apply(lambda amount: f"-{amount:.2f}".replace(".", ","))

        return clean_df

    def write_output_file(self, clean_df: pd.DataFrame) -> None:
        """
        Write the extracted dataframe to a csv file in the raw data
        directory, quoting the amount column to preserve its comma decimal
        separator.

        Args:
            clean_df (pd.DataFrame): dataframe to write.
        """
        result_dir = "src/data/raw"
        curr_dir = os.getcwd()
        file_name = re.split(r"[\/\\]", self.file_path)[-1].rsplit(
            ".csv", 1
        )[0]

        if os.path.exists(result_dir):
            output_path = f"./{result_dir}/{file_name}_subset_reformatted.csv"
        else:
            full_path = os.path.join(curr_dir, result_dir)
            os.makedirs(full_path)
            output_path = f"{full_path}/{file_name}_subset_reformatted.csv"

        with open(output_path, "w", newline="") as output_file:
            output_file.write(";".join(clean_df.columns) + "\n")
            for row in clean_df.itertuples(index=False):
                output_file.write(
                    f"{row[0]};{row[1]};\"{row[2]}\";{row[3]}\n"
                )

        print(
            "Wise transactions have been successfully extracted and saved."
        )
