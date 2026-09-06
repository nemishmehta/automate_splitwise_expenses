from typing import Dict, Iterable, List, Optional

from src.core.backend import ExpenseBackend
from src.core.models import Category, Expense, Group, Participant


class FakeExpenseBackend(ExpenseBackend):
    """
    In-memory ExpenseBackend for tests: seeded with Groups and Categories up
    front, and records every Expense passed to create_expense for tests to
    assert against.
    """

    def __init__(
        self,
        groups: Optional[Iterable[Group]] = None,
        categories: Optional[Iterable[Category]] = None,
    ) -> None:
        self._groups: Dict[str, Group] = {
            group.id: group for group in (groups or [])
        }
        self._categories: List[Category] = list(categories or [])
        self.created_expenses: List[Expense] = []

    def list_groups(self) -> List[Group]:
        return list(self._groups.values())

    def list_participants(self, group_id: str) -> List[Participant]:
        return list(self._groups[group_id].participants)

    def list_categories(self) -> List[Category]:
        return list(self._categories)

    def create_expense(self, expense: Expense) -> None:
        self.created_expenses.append(expense)
