from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Tuple

from src.core.backend import ExpenseBackend
from src.core.default_split_profile import (
    DefaultSplitProfileStore,
    SplitProfile,
)
from src.core.models import Expense, Group, Participant, Split, SplitMethod
from src.core.split import (
    compute_equal_split,
    compute_exact_split,
    compute_percentage_split,
)
from src.core.transactions import read_transactions_csv


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


class PersonalExpenseCLI:
    """
    Thin interface layer over the core: reads a cleaned CSV, reviews each
    transaction with the owner one at a time, and submits confirmed ones as
    a Personal Expense (a Group containing only the owner) through the
    given ExpenseBackend. Gathers input and calls the core/backend only -
    no split/category/expense-construction business logic lives here.
    """

    def __init__(
        self,
        backend: ExpenseBackend,
        group_id: str,
        csv_path: Path,
        input_fn: Callable[[str], str] = input,
        print_fn: Callable[..., None] = print,
    ) -> None:
        self._backend = backend
        self._group_id = group_id
        self._csv_path = csv_path
        self._input = input_fn
        self._print = print_fn

    def run(self) -> None:
        payer_id = self._resolve_payer_id()
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

            self._print("\nSubmit as a Personal Expense:")
            self._print(f"  Group: {self._group_id}")
            self._print(f"  Date: {transaction.date}")
            self._print(
                f"  Amount: {transaction.amount} {transaction.currency}"
            )
            self._print(f"  Description: {transaction.description}")
            confirm_choice = self._input(
                "\nPress Enter to submit this Expense, or any other key "
                "to cancel - "
            )
            if confirm_choice != "":
                summary.skipped += 1
                continue

            expense = Expense(
                group_id=self._group_id,
                description=transaction.description,
                amount=transaction.amount,
                currency=transaction.currency,
                date=transaction.date,
                payer_id=payer_id,
                category_id=None,
                split=None,
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

    def _resolve_payer_id(self) -> str:
        participants = self._backend.list_participants(self._group_id)
        if len(participants) != 1:
            raise ValueError(
                f"Group {self._group_id} is not a Personal Expense Group "
                f"(expected exactly 1 Participant, found "
                f"{len(participants)})."
            )
        return participants[0].id


class SharedExpenseCLI:
    """
    Thin interface layer over the core for Shared Expenses: reviews each
    transaction from the cleaned CSV, lets the owner choose a Group (other
    than a Personal Expense Group), a subset of 2+ of that Group's
    Participants, and a split method (Equal, Exact Amount, or Percentage),
    computes the resulting Split, and submits it through the given
    ExpenseBackend.
    """

    def __init__(
        self,
        backend: ExpenseBackend,
        payer_ids: Mapping[str, str],
        csv_path: Path,
        input_fn: Callable[[str], str] = input,
        print_fn: Callable[..., None] = print,
        default_split_profiles: Optional[DefaultSplitProfileStore] = None,
    ) -> None:
        self._backend = backend
        self._payer_ids = payer_ids
        self._csv_path = csv_path
        self._input = input_fn
        self._print = print_fn
        self._default_split_profiles = default_split_profiles

    def run(self) -> None:
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
            participant_ids = self._choose_participants(group, payer_id)
            split = self._choose_split(
                group, participant_ids, transaction.amount, payer_id
            )

            self._print("\nSubmit as a Shared Expense:")
            self._print(f"  Group: {group.name}")
            self._print(f"  Date: {transaction.date}")
            self._print(
                f"  Amount: {transaction.amount} {transaction.currency}"
            )
            self._print(f"  Description: {transaction.description}")
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
                category_id=None,
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

    def _shared_groups(self) -> List[Group]:
        return [
            group
            for group in self._backend.list_groups()
            if len(group.participants) >= 2
        ]

    def _choose_group(self) -> Group:
        groups = self._shared_groups()
        self._print("\nChoose a Group for this Shared Expense:")
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
