import csv
import os
import re
from datetime import date
from typing import Dict, List

import pandas as pd


class CleanCsv:
    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path

    def run_pipeline(self):

        with open(self.file_path) as csv_file:
            dialect = csv.Sniffer().sniff(csv_file.read(1024))

        raw_df: pd.DataFrame = pd.read_csv(
            self.file_path, sep=dialect.delimiter
        )
        raw_headers: List[str] = [col for col in raw_df]
        mapped_headers: Dict[str, str] = self.map_headers(raw_headers)
        clean_df: pd.DataFrame = self.clean_values(raw_df, mapped_headers)

        self.write_output_file(clean_df)

    def map_headers(self, raw_headers) -> Dict[str, str]:
        """
        Request users to identify headers from given csv that match date,
        amount, description.

        Args:
            raw_headers (List[str]): list of headers extracted from provided
            csv.

        Returns:
            Dict[str, str]: dictionary mapping csv headers to date, amount,
            description, currency fields.
        """

        mapped_headers: Dict[str, str] = {
            "date": "",
            "amount": "",
            "description": "",
        }

        for key in mapped_headers.keys():
            for index, item in enumerate(raw_headers):
                print(index, item)

            while mapped_headers[key] == "":
                try:
                    raw_headers_index: int = int(
                        input(f"Enter the number that matches {key} header - ")
                    )
                    mapped_headers[key] = raw_headers[raw_headers_index]
                except ValueError:
                    print("Please enter a valid number.")
                except IndexError:
                    print("Please enter a value within the given list.")

        return mapped_headers

    def clean_values(
        self, raw_df: pd.DataFrame, mapped_headers: List[str]
    ) -> pd.DataFrame:
        """
        Return clean values for date, amount, description and currency columns.
        Args:
            raw_df (pd.DataFrame): raw dataframe
            mapped_headers (List[str]): mapped headers

        Returns:
            pd.DataFrame: dataframe with clean values
        """
        raw_df_only_reqd_columns: pd.DataFrame = self.return_reqd_columns(
            raw_df, mapped_headers
        )

        clean_amount_df: pd.DataFrame = self.clean_amount_values(
            raw_df_only_reqd_columns
        )

        clean_description_df: pd.DataFrame = self.clean_description_values(
            clean_amount_df
        )

        clean_df: pd.DataFrame = self.clean_date_values(clean_description_df)

        return clean_df

    def return_reqd_columns(
        self, raw_df: pd.DataFrame, mapped_headers: List[str]
    ) -> pd.DataFrame:
        """_summary_

        Args:
            raw_df (pd.DataFrame): _description_
            mapped_headers (List[str]): _description_

        Returns:
            pd.DataFrame: _description_
        """
        raw_df_only_reqd_columns: pd.DataFrame = raw_df[
            [
                mapped_headers["date"],
                mapped_headers["amount"],
                mapped_headers["description"],
            ]
        ].copy()

        for key in mapped_headers.keys():
            raw_df_only_reqd_columns.rename(
                columns={mapped_headers[key]: key}, inplace=True
            )

        return raw_df_only_reqd_columns

    def clean_amount_values(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        1. Remove missing amount values.
        2. Remove negative, positive, and empty spaces from amount values.
        3. Replace , with . in amount values
        Args:
            raw_df (pd.DataFrame): raw dataframe

        Returns:
            pd.DataFrame: dataframe with clean amount values
        """
        clean_df: pd.DataFrame = self.drop_null_amount_values(raw_df)

        for index, amount in enumerate(clean_df["amount"]):
            amount: str = str(amount)
            if amount.startswith("-"):
                clean_amount: str = self.clean_value(amount)
                clean_df.at[index, "amount"] = clean_amount

            elif amount.startswith("+"):
                print(clean_df.loc[[index]])
                valid_responses: List[str] = ["y", "N"]
                user_input: str = ""

                while user_input not in valid_responses:
                    user_input = input(
                        "Do you want to keep this expense [y/N]? - "
                    )
                    print("\n")

                if user_input == "y":
                    clean_amount: str = self.clean_value(amount)
                    clean_df.at[index, "amount"] = clean_amount
                elif user_input == "N":
                    clean_df.drop(clean_df.index[index], inplace=True)

            else:
                clean_amount: str = self.clean_value(amount)
                clean_df.at[index, "amount"] = clean_amount

        return clean_df.reset_index(drop=True)

    def drop_null_amount_values(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns a dataframe after dropping rows with null amount values.

        Args:
            raw_df (pd.DataFrame): raw dataframe

        Returns:
            pd.DataFrame: dataframe with no rows of null amount values
        """
        print(
            (
                "The following rows have no amount values so they will not be "
                "considered."
            )
        )
        print(raw_df[raw_df["amount"].isna()])
        print("----------------------------------------------------\n")
        clean_df = raw_df.dropna(subset="amount").reset_index(drop=True)

        return clean_df

    def clean_value(self, amount: str) -> str:
        """
        Identify only amount value in given string and replace ',' with '.'
        Args:
            amount (str): raw amount string

        Returns:
            str: clean amount string
        """
        clean_amount: str = (
            re.search(r"\d+,\d+", amount).group().replace(",", ".")
        )
        return clean_amount

    def clean_description_values(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
            Replace missing values in description either with user input or
            default value.
        Args:
            raw_df (pd.DataFrame): raw dataframe

        Returns:
            pd.DataFrame: dataframe with clean description values
        """
        raw_df["description"] = raw_df["description"].fillna("")

        for index, desc in enumerate(raw_df["description"]):
            if desc == "":
                print(raw_df.loc[[index]])
                clean_desc = input(
                    (
                        "Please provide a description or "
                        "press Enter to input default value (Expense) - "
                    )
                )
                if clean_desc != "":
                    raw_df.at[index, "description"] = clean_desc
                else:
                    raw_df.at[index, "description"] = "Expense"
                print("\n")

        return raw_df

    def clean_date_values(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
            Replace missing values in date either with user input or default
            value.

        Args:
            raw_df (pd.DataFrame): raw dataframe

        Returns:
            pd.DataFrame: dataframe with clean date values.
        """
        raw_df["date"] = raw_df["date"].fillna("")

        for index, raw_date in enumerate(raw_df["date"]):
            if raw_date == "":
                print(raw_df.loc[[index]])
                clean_date = input(
                    (
                        "Please provide a date (DD/MM/YYYY) or "
                        "press Enter to input default value (current date) - "
                    )
                )
                if clean_date != "":
                    raw_df.at[index, "date"] = clean_date
                else:
                    raw_df.at[index, "date"] = date.today().strftime(
                        "%d/%m/%Y"
                    )
                print("\n")

        return raw_df

    def write_output_file(self, clean_df: pd.DataFrame) -> None:
        """
        Write clean dataframe to csv file.

        Args:
            clean_df (pd.DataFrame): clean dataframe
        """
        result_dir = "src/data/clean"
        curr_dir = os.getcwd()
        file_name = self.file_path.rsplit("/", 1)[-1].rsplit(".csv", 1)[0]
        if os.path.exists(result_dir):
            clean_df.to_csv(
                f"./{result_dir}/{file_name}_clean.csv", index=False
            )
        else:
            full_path = os.path.join(curr_dir, result_dir)
            os.makedirs(full_path)
            clean_df.to_csv(f"{full_path}/{file_name}_clean.csv", index=False)


test_class = CleanCsv("./tests/data/raw/test_data_raw.csv")
test_class.run_pipeline()
