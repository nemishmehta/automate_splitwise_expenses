import csv
import os
import re
from datetime import date
from typing import Dict, List

import pandas as pd


class CleanCsv:
    def __init__(self, file_path: str) -> None:
        self.file_path: str = str(file_path)

    def run_pipeline(self) -> None:

        print("Cleaning csv.\n")
        try:
            with open(self.file_path) as csv_file:
                dialect = csv.Sniffer().sniff(csv_file.read(1024))

            delimiter = dialect.delimiter
            raw_df: pd.DataFrame = pd.read_csv(self.file_path, sep=delimiter)
        except Exception:
            delimiter = input(
                (
                    "The program was not able to detect the delimiter "
                    "automatically. "
                    "Please provide the delimiter (,|;|space|tab) - "
                )
            )
            raw_df: pd.DataFrame = pd.read_csv(self.file_path, sep=delimiter)
        raw_headers: List[str] = [col for col in raw_df]

        mapped_headers: Dict[str, str] = self.map_headers(raw_headers)

        clean_df: pd.DataFrame = self.clean_values(raw_df, mapped_headers)

        self.write_output_file(clean_df)

    def map_headers(self, raw_headers: List[str]) -> Dict[str, str]:
        """
        Request users to identify headers from given csv that match date,
        amount, description, currency.

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
            "currency": "",
        }

        print("\nStep 1: Let's identify the required columns.\n")
        print(
            (
                "Given below are the columns from your csv with a number "
                "assigned to each. Provide the relevant number for the "
                "following questions.\n"
            )
        )
        for key in mapped_headers.keys():
            for index, item in enumerate(raw_headers):
                print(f"{index} - {item}")

            while mapped_headers[key] == "":
                try:
                    raw_headers_index: int = int(
                        input(
                            (
                                f"\nEnter the number that matches the {key} "
                                "column - "
                            )
                        )
                    )
                    mapped_headers[key] = raw_headers[raw_headers_index]
                except ValueError:
                    print("\nPlease enter a valid number.")
                except IndexError:
                    print("\nPlease enter a value within the given list.")
                finally:
                    print("\n")
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
        """
        Return raw dataframe with only required columns.

        Args:
            raw_df (pd.DataFrame): raw dataframe created from csv file.
            mapped_headers (List[str]): required headers.

        Returns:
            pd.DataFrame: raw dataframe with only required columns.
        """
        raw_df_only_reqd_columns: pd.DataFrame = raw_df[
            [
                mapped_headers["date"],
                mapped_headers["amount"],
                mapped_headers["description"],
                mapped_headers["currency"],
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
        print("Cleaning amount column.\n")
        clean_df: pd.DataFrame = self.drop_null_amount_values(raw_df)

        values_wo_sign = len(
            clean_df[
                (~clean_df["amount"].str.startswith("-"))
                & (~clean_df["amount"].str.startswith("+"))
            ]
        )
        if values_wo_sign > 0:
            clean_df = self.clean_amount_wo_sign(clean_df)

        values_with_pos_values = len(
            clean_df[clean_df["amount"].str.startswith("+")]
        )
        if values_with_pos_values > 0:
            clean_df = self.clean_amount_with_pos_sign(clean_df)

        clean_df["amount"] = clean_df["amount"].apply(
            lambda x: self.clean_value(x)
        )

        return clean_df.reset_index(drop=True)

    def drop_null_amount_values(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns a dataframe after dropping rows with null amount values.

        Args:
            raw_df (pd.DataFrame): raw dataframe

        Returns:
            pd.DataFrame: dataframe with no rows of null amount values
        """
        total_empty_amount_vals = raw_df["amount"].isna().sum()
        if total_empty_amount_vals > 0:
            print("Dropping empty amount values.\n")
            print(
                (
                    "The following rows have no amount values so they will be "
                    "discarded.\n"
                )
            )
            print(raw_df[raw_df["amount"].isna()])
            print("\n----------------------------------------------------\n")

        clean_df = raw_df.dropna(subset="amount").reset_index(drop=True)

        return clean_df

    def clean_amount_wo_sign(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify all amount values without any sign and ask user if they want
        to keep or discard the values.

        Args:
            df (pd.DataFrame): raw dataframe

        Returns:
            pd.DataFrame: dataframe with/without amount values with no sign
            depending on user's choice.
        """
        print("Cleaning amounts with no sign.\n")
        print(
            df.loc[
                (~df["amount"].str.startswith("-"))
                & (~df["amount"].str.startswith("+"))
            ]
        )
        user_input = input(
            (
                "\nThe above transactions do not have any sign (+|-) in "
                "the amount column. Are these expenses that need to be kept "
                "[y|N]? - "
            )
        )
        if user_input == "N":
            amount_wo_sign_df = df[
                (df["amount"].str.startswith("-"))
                | (df["amount"].str.startswith("+"))
            ]
            return amount_wo_sign_df
        else:
            return df

    def clean_amount_with_pos_sign(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify all amount values with a positive sign and ask user if they
        want to keep or discard the values.

        Args:
            df (pd.DataFrame): raw dataframe

        Returns:
            pd.DataFrame: dataframe with/without amount values with positive
            sign depending on user's choice.
        """
        print("\nCleaning amounts with positive sign.\n")
        print(df.loc[df["amount"].str.startswith("+")])
        user_input = input(
            (
                "\nThe above transactions have a positive sign in "
                "the amount column. Press enter to discard them or any other "
                "key to keep the values - "
            )
        )
        if user_input == "":
            amount_wo_pos_sign_df = df[~df["amount"].str.startswith("+")]
            return amount_wo_pos_sign_df
        else:
            return df

    def clean_value(self, amount: str) -> str:
        """
        Identify only amount value in given string and replace ',' with '.'
        Args:
            amount (str): raw amount string

        Returns:
            str: clean amount string
        """
        amount_wo_fullstop = amount.replace(".", "")
        clean_amount: str = (
            re.search(r"\d+,\d+", amount_wo_fullstop).group().replace(",", ".")
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
        total_empty_desc_vals = raw_df["description"].isna().sum()
        if total_empty_desc_vals > 0:
            print("\nCleaning description column values.\n")

            raw_df["description"] = raw_df["description"].fillna("")

            for index, desc in enumerate(raw_df["description"]):
                if desc == "":
                    print(raw_df.loc[[index]])
                    clean_desc = input(
                        (
                            "\nThe above transaction is missing a description."
                            " Please provide one or "
                            "press Enter to input default value (Expense) - "
                        )
                    )
                    if clean_desc != "":
                        raw_df.at[index, "description"] = clean_desc
                    else:
                        raw_df.at[index, "description"] = "Expense"

            return raw_df
        else:
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
        total_empty_date_vals = raw_df["date"].isna().sum()
        if total_empty_date_vals > 0:
            print("\nCleaning date column values.\n")

            raw_df["date"] = raw_df["date"].fillna("")

            for index, raw_date in enumerate(raw_df["date"]):
                if raw_date == "":
                    print(raw_df.loc[[index]])
                    clean_date = input(
                        (
                            "\nThe above transaction is missing a date. "
                            "Please provide a date (DD/MM/YYYY) or "
                            "press Enter to input default value (current date)"
                            " - "
                        )
                    )
                    if clean_date != "":
                        raw_df.at[index, "date"] = clean_date
                    else:
                        raw_df.at[index, "date"] = date.today().strftime(
                            "%d/%m/%Y"
                        )

            return raw_df
        else:
            return raw_df

    def write_output_file(self, clean_df: pd.DataFrame) -> None:
        """
        Write clean dataframe to csv file.

        Args:
            clean_df (pd.DataFrame): clean dataframe
        """
        result_dir = "src/data/clean"
        curr_dir = os.getcwd()
        file_name = re.split(r"[\/\\]", self.file_path)[-1].rsplit(".csv", 1)[
            0
        ]
        if os.path.exists(result_dir):
            clean_df.to_csv(
                f"./{result_dir}/{file_name}_clean.csv", index=False, sep=";"
            )
        else:
            full_path = os.path.join(curr_dir, result_dir)
            os.makedirs(full_path)
            clean_df.to_csv(
                f"{full_path}/{file_name}_clean.csv", index=False, sep=";"
            )
