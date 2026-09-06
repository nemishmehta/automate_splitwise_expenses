from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from src.core.backend import ExpenseBackend
from src.core.category_suggestion import (
    CategorySuggestionHistory,
    KeywordRule,
    suggest_category,
)
from src.core.default_split_profile import (
    DefaultSplitProfileStore,
    SplitProfile,
)
from src.core.models import (
    Category,
    Expense,
    Group,
    Participant,
    Split,
    SplitMethod,
)
from src.core.split import (
    compute_equal_split,
    compute_exact_split,
    compute_percentage_split,
)
from src.core.transactions import read_transactions_csv


def _resolve_category(
    description: str,
    categories: List[Category],
    category_suggestions: Optional[CategorySuggestionHistory],
    keyword_rules: Iterable[KeywordRule],
    input_fn: Callable[[str], str],
    print_fn: Callable[..., None],
) -> Optional[str]:
    """
    Resolve the Category for an Expense: pre-fill and offer one-keypress
    confirmation for a suggestion from `suggest_category`, falling through
    to a manual choice (recorded as an override) when declined or when no
    suggestion exists. Skipped entirely when there's nothing to choose
    from (no suggestion and no Categories at all).
    """
    suggested_id = None
    if category_suggestions is not None:
        suggested_id = suggest_category(
            description, category_suggestions, keyword_rules
        )

    if suggested_id is not None:
        print_fn(
            f"\nSuggested Category: "
            f"{_category_name(categories, suggested_id)}"
        )
        choice = input_fn(
            "Press Enter to accept this Category, or any other key to "
            "choose a different one - "
        )
        if choice == "":
            return suggested_id

    if not categories:
        return None

    category_id = _prompt_category_choice(categories, input_fn, print_fn)
    if category_id is not None and category_suggestions is not None:
        category_suggestions.record(description, category_id)
    return category_id


def _prompt_category_choice(
    categories: List[Category],
    input_fn: Callable[[str], str],
    print_fn: Callable[..., None],
) -> Optional[str]:
    print_fn("\nChoose a Category:")
    print_fn("  0. None")
    for position, category in enumerate(categories, start=1):
        print_fn(f"  {position}. {category.name}")
    choice = input_fn("Enter a number - ")
    if choice in ("", "0"):
        return None
    return categories[int(choice) - 1].id


def _category_name(
    categories: List[Category], category_id: Optional[str]
) -> str:
    if category_id is None:
        return "None"
    for category in categories:
        if category.id == category_id:
            return category.name
    return category_id


@dataclass
class _RunSummary:
    total: int = 0
    submitted: int = 0
    skipped: int = 0
    failed: int = 0

    def as_line(self) -> str:
        return (
            f"Done. {self.submitted} submitted, {self.skipped} skipped, "
            f"{self.failed} failed, out of {self.total} total."
        )


class ExpenseCLI:
    """
    Thin interface layer over the core covering every Expense type: reads a
    cleaned CSV, reviews each transaction with the owner one at a time, and
    lets them choose which registered Group it belongs to. That Group's
    Participant count alone then decides the rest of the prompts - exactly
    1 Participant submits a Personal Expense with no participant-selection
    or Split-method prompts (`split=None`); 2+ Participants runs the Shared
    Expense flow (choose Participants, choose Split, Default Split Profile
    pre-fill). A single run can freely mix both. Gathers input and calls
    the core/backend only - no split/category/expense-construction
    business logic lives here.
    """

    def __init__(
        self,
        backend: ExpenseBackend,
        payer_ids: Mapping[str, str],
        csv_path: Path,
        input_fn: Callable[[str], str] = input,
        print_fn: Callable[..., None] = print,
        default_split_profiles: Optional[DefaultSplitProfileStore] = None,
        category_suggestions: Optional[CategorySuggestionHistory] = None,
        keyword_rules: Optional[Iterable[KeywordRule]] = None,
    ) -> None:
        self._backend = backend
        self._payer_ids = payer_ids
        self._csv_path = csv_path
        self._input = input_fn
        self._print = print_fn
        self._default_split_profiles = default_split_profiles
        self._category_suggestions = category_suggestions
        self._keyword_rules = keyword_rules or []

    def run(self) -> None:
        categories = self._backend.list_categories()
        transactions = read_transactions_csv(self._csv_path)
        summary = _RunSummary(total=len(transactions))

        self._print(f"\nThere are {summary.total} transactions to review.")

        for index, transaction in enumerate(transactions, start=1):
            self._print(f"\nTransaction {index}/{summary.total}")
            self._print(f"  Date: {transaction.date}")
            self._print(
                f"  Amount: {transaction.amount} {transaction.currency}"
            )
            self._print(f"  Description: {transaction.description}")

            review_choice = self._input(
                "\nPress Enter to review this transaction, or any other "
                "key to skip it - "
            )
            if review_choice != "":
                summary.skipped += 1
                continue

            group = self._choose_group()
            payer_id = self._payer_ids[group.id]

            if len(group.participants) == 1:
                split = None
                expense_kind = "Personal Expense"
            else:
                participant_ids = self._choose_participants(group, payer_id)
                split = self._choose_split(
                    group, participant_ids, transaction.amount, payer_id
                )
                expense_kind = "Shared Expense"

            category_id = _resolve_category(
                transaction.description,
                categories,
                self._category_suggestions,
                self._keyword_rules,
                self._input,
                self._print,
            )

            self._print(f"\nSubmit as a {expense_kind}:")
            self._print(f"  Group: {group.name}")
            self._print(f"  Date: {transaction.date}")
            self._print(
                f"  Amount: {transaction.amount} {transaction.currency}"
            )
            self._print(f"  Description: {transaction.description}")
            self._print(
                f"  Category: {_category_name(categories, category_id)}"
            )
            if split is not None:
                for share in split.shares:
                    self._print(
                        f"  Share: {share.participant_id} owes "
                        f"{share.owed_amount}"
                    )
            confirm_choice = self._input(
                "\nPress Enter to submit this Expense, or any other key "
                "to cancel - "
            )
            if confirm_choice != "":
                summary.skipped += 1
                continue

            expense = Expense(
                group_id=group.id,
                description=transaction.description,
                amount=transaction.amount,
                currency=transaction.currency,
                date=transaction.date,
                payer_id=payer_id,
                category_id=category_id,
                split=split,
            )
            try:
                self._backend.create_expense(expense)
            except Exception as error:
                self._print(f"Failed to submit Expense: {error}")
                summary.failed += 1
            else:
                self._print("Expense successfully submitted.")
                summary.submitted += 1

        self._print(f"\n{summary.as_line()}")

    def _registered_groups(self) -> List[Group]:
        return [
            group
            for group in self._backend.list_groups()
            if group.id in self._payer_ids
        ]

    def _choose_group(self) -> Group:
        groups = self._registered_groups()
        self._print("\nChoose a Group for this Expense:")
        for position, group in enumerate(groups, start=1):
            self._print(f"  {position}. {group.name}")
        choice = self._input("Enter a number - ")
        return groups[int(choice) - 1]

    def _choose_participants(self, group: Group, payer_id: str) -> List[str]:
        others: List[Participant] = [
            participant
            for participant in group.participants
            if participant.id != payer_id
        ]
        self._print("\nChoose who else shares this Expense:")
        for position, participant in enumerate(others, start=1):
            self._print(f"  {position}. {participant.name}")
        choice = self._input(
            "Enter comma-separated numbers for the other Participants - "
        )
        chosen_positions = [int(part.strip()) for part in choice.split(",")]
        chosen_other_ids = [
            others[position - 1].id for position in chosen_positions
        ]
        return [payer_id] + chosen_other_ids

    def _choose_split(
        self,
        group: Group,
        participant_ids: List[str],
        total: Decimal,
        payer_id: str,
    ) -> Split:
        default_split = self._use_default_split(
            participant_ids, total, payer_id
        )
        if default_split is not None:
            return default_split

        self._print("\nChoose a split method:")
        self._print("  1. Equal")
        self._print("  2. Exact Amount")
        self._print("  3. Percentage")
        choice = self._input("Enter a number - ")

        if choice == "1":
            split = compute_equal_split(participant_ids, total, payer_id)
            self._record_default_split(participant_ids, split, values=None)
            return split
        if choice == "2":
            values, split = self._prompt_split(
                group,
                participant_ids,
                label="an exact amount",
                compute=lambda shares: compute_exact_split(
                    shares, total, payer_id
                ),
            )
            self._record_default_split(participant_ids, split, values)
            return split
        values, split = self._prompt_split(
            group,
            participant_ids,
            label="a percentage",
            compute=lambda shares: compute_percentage_split(
                shares, total, payer_id
            ),
        )
        self._record_default_split(participant_ids, split, values)
        return split

    def _use_default_split(
        self, participant_ids: List[str], total: Decimal, payer_id: str
    ) -> Optional[Split]:
        if self._default_split_profiles is None:
            return None

        profile = self._default_split_profiles.get(participant_ids)
        if profile is None:
            return None

        self._print(
            f"\nDefault Split found: {profile.method.value}"
            + (f" {dict(profile.values)}" if profile.values else "")
        )
        choice = self._input(
            "Press Enter to use this Default Split, or any other key to "
            "choose a different split - "
        )
        if choice != "":
            return None

        if profile.method == SplitMethod.EQUAL:
            return compute_equal_split(participant_ids, total, payer_id)
        if profile.method == SplitMethod.EXACT:
            return compute_exact_split(profile.values, total, payer_id)
        return compute_percentage_split(profile.values, total, payer_id)

    def _record_default_split(
        self,
        participant_ids: List[str],
        split: Split,
        values: Optional[Mapping[str, Decimal]],
    ) -> None:
        if self._default_split_profiles is None:
            return

        self._default_split_profiles.record(
            participant_ids,
            SplitProfile(
                method=split.method,
                values=dict(values) if values else None,
            ),
        )

    def _prompt_split(
        self,
        group: Group,
        participant_ids: List[str],
        label: str,
        compute: Callable[[Mapping[str, Decimal]], Split],
    ) -> Tuple[Dict[str, Decimal], Split]:
        id_to_name = {
            participant.id: participant.name
            for participant in group.participants
        }
        self._print(f"\nEnter {label} for each Participant:")
        for participant_id in participant_ids:
            self._print(f"  {id_to_name[participant_id]}")

        while True:
            raw = self._input("Enter comma-separated values, in that order - ")
            try:
                values = [Decimal(part.strip()) for part in raw.split(",")]
                shares = dict(zip(participant_ids, values))
                return shares, compute(shares)
            except (InvalidOperation, ValueError) as error:
                self._print(f"Invalid entry: {error}")
