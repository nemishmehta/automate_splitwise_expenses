import argparse
from pathlib import Path

from src.core.category_suggestion import (
    CategorySuggestionHistory,
    load_keyword_rules,
)
from src.main.expense_cli import PersonalExpenseCLI
from src.spliit.backend import SpliitExpenseBackend

CATEGORY_HISTORY_PATH = (
    Path(__file__).resolve().parents[2] / "category_suggestion_history.json"
)
KEYWORD_RULES_PATH = (
    Path(__file__).resolve().parents[2] / "category_keyword_rules.json"
)

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
            category_suggestions=CategorySuggestionHistory(
                CATEGORY_HISTORY_PATH
            ),
            keyword_rules=load_keyword_rules(KEYWORD_RULES_PATH),
        )
        cli.run()
