import argparse
from pathlib import Path

from src.core.default_split_profile import DefaultSplitProfileStore
from src.main.expense_cli import SharedExpenseCLI
from src.spliit.backend import SpliitExpenseBackend
from src.spliit.who_am_i import WhoAmI

WHO_AM_I_PATH = Path(__file__).resolve().parents[2] / "who_am_i.json"
DEFAULT_SPLIT_PROFILES_PATH = (
    Path(__file__).resolve().parents[2] / "default_split_profiles.json"
)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Review a cleaned CSV of transactions and submit chosen ones "
            "as Shared Expenses, equally split across a chosen subset of "
            "a chosen Group's Participants."
        )
    )
    parser.add_argument(
        "--group-id",
        required=True,
        action="append",
        dest="group_ids",
        help=(
            "Spliit Group id to offer as a Shared Expense choice. Repeat "
            "for multiple Groups."
        ),
    )
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()

    if not args.csv_path.exists():
        print(f"The given filepath is incorrect - {args.csv_path}")
    else:
        who_am_i = WhoAmI(WHO_AM_I_PATH)
        payer_ids = {
            group_id: who_am_i.get(group_id) for group_id in args.group_ids
        }
        missing = [
            group_id
            for group_id, payer_id in payer_ids.items()
            if payer_id is None
        ]
        if missing:
            print(
                "No Payer Configuration found for Group(s) "
                f"{missing}. Run run_configure_who_am_i.py for each "
                "first."
            )
        else:
            backend = SpliitExpenseBackend(group_ids=args.group_ids)
            default_split_profiles = DefaultSplitProfileStore(
                DEFAULT_SPLIT_PROFILES_PATH
            )
            cli = SharedExpenseCLI(
                backend=backend,
                payer_ids=payer_ids,
                csv_path=args.csv_path,
                default_split_profiles=default_split_profiles,
            )
            cli.run()
