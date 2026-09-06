import argparse
from pathlib import Path

from src.core.category_suggestion import (
    CategorySuggestionHistory,
    load_keyword_rules,
)
from src.core.default_split_profile import DefaultSplitProfileStore
from src.main.expense_cli import ExpenseCLI
from src.spliit.backend import SpliitExpenseBackend
from src.spliit.who_am_i import WhoAmI

WHO_AM_I_PATH = Path(__file__).resolve().parents[2] / "who_am_i.json"
DEFAULT_SPLIT_PROFILES_PATH = (
    Path(__file__).resolve().parents[2] / "default_split_profiles.json"
)
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
            "as Expenses. Every registered Group is offered per "
            "transaction; a Group with exactly 1 Participant submits a "
            "Personal Expense, 2+ Participants runs the Shared Expense "
            "flow - a single run can mix both."
        )
    )
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"The given filepath is incorrect - {args.csv_path}")
    else:
        who_am_i = WhoAmI(WHO_AM_I_PATH)
        group_ids = who_am_i.known_group_ids()

        if not group_ids:
            print(
                "No Groups have a Payer Configuration yet. Run "
                "run_configure_who_am_i.py --group-id <id> to register a "
                "Group first."
            )
        else:
            payer_ids = {
                group_id: who_am_i.get(group_id) for group_id in group_ids
            }
            backend = SpliitExpenseBackend(
                group_ids=group_ids,
                on_group_error=lambda group_id, exc: print(
                    f"Warning: skipping Group {group_id} "
                    f"({exc}); continuing with the remaining Groups."
                ),
            )
            if not backend.list_groups():
                print(
                    "None of the registered Groups could be fetched from "
                    "Spliit. Check the warnings above, or register a new "
                    "Group with run_configure_who_am_i.py."
                )
            else:
                default_split_profiles = DefaultSplitProfileStore(
                    DEFAULT_SPLIT_PROFILES_PATH
                )
                cli = ExpenseCLI(
                    backend=backend,
                    payer_ids=payer_ids,
                    csv_path=args.csv_path,
                    default_split_profiles=default_split_profiles,
                    category_suggestions=CategorySuggestionHistory(
                        CATEGORY_HISTORY_PATH
                    ),
                    keyword_rules=load_keyword_rules(KEYWORD_RULES_PATH),
                )
                cli.run()
