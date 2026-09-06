from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Mapping

from src.core.backend import ExpenseBackend
from src.core.models import Expense, Group, Participant
from src.core.split import compute_equal_split
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
    than a Personal Expense Group) and a subset of 2+ of that Group's
    Participants, computes an Equal split across the chosen set, and
    submits the result through the given ExpenseBackend.
    """

    def __init__(
        self,
        backend: ExpenseBackend,
        payer_ids: Mapping[str, str],
        csv_path: Path,
        input_fn: Callable[[str], str] = input,
        print_fn: Callable[..., None] = print,
    ) -> None:
        self._backend = backend
        self._payer_ids = payer_ids
        self._csv_path = csv_path
        self._input = input_fn
        self._print = print_fn

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
            split = compute_equal_split(
                participant_ids, transaction.amount, payer_id
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

    def _choose_participants(
        self, group: Group, payer_id: str
    ) -> List[str]:
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
