from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from src.core.backend import ExpenseBackend
from src.core.models import Expense
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
