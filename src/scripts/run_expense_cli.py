import argparse
from pathlib import Path

from src.main.expense_cli import PersonalExpenseCLI
from src.spliit.backend import SpliitExpenseBackend

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Review a cleaned CSV of transactions and submit chosen ones "
            "as Personal Expenses against a Spliit Group containing only "
            "yourself."
        )
    )
    parser.add_argument(
        "--group-id",
        required=True,
        help="Spliit Group id for your Personal Expense Group.",
    )
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"The given filepath is incorrect - {args.csv_path}")
    else:
        backend = SpliitExpenseBackend(group_ids=[args.group_id])
        cli = PersonalExpenseCLI(
            backend=backend,
            group_id=args.group_id,
            csv_path=args.csv_path,
        )
        cli.run()
