from abc import ABC, abstractmethod
from typing import List

from src.core.models import Category, Expense, Group, Participant


class ExpenseBackend(ABC):
    """
    Backend-agnostic surface an expense-tracking service must implement so
    the core domain logic never depends on a specific backend's SDK.
    """

    @abstractmethod
    def list_groups(self) -> List[Group]:
        ...

    @abstractmethod
    def list_participants(self, group_id: str) -> List[Participant]:
        ...

    @abstractmethod
    def list_categories(self) -> List[Category]:
        ...

    @abstractmethod
    def create_expense(self, expense: Expense) -> None:
        ...
