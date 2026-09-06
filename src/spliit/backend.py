from decimal import Decimal
from typing import Iterable, List, Tuple

from src.core.backend import ExpenseBackend
from src.core.models import Category, Expense, Group, Participant
from src.spliit.client import SpliitClient, SplitMode

# Spliit has no live endpoint to fetch Categories from - the hosted app
# ships this fixed taxonomy client-side (mirrored here from the
# spliit-api-client 0.1.1 package's own hardcoded `CATEGORIES` dict).
_CATEGORY_GROUPS = {
    "Uncategorized": {"General": 0, "Payment": 1},
    "Entertainment": {
        "Entertainment": 2,
        "Games": 3,
        "Movies": 4,
        "Music": 5,
        "Sports": 6,
    },
    "Food and Drink": {
        "Food and Drink": 7,
        "Dining Out": 8,
        "Groceries": 9,
        "Liquor": 10,
    },
    "Home": {
        "Home": 11,
        "Electronics": 12,
        "Furniture": 13,
        "Household Supplies": 14,
        "Maintenance": 15,
        "Mortgage": 16,
        "Pets": 17,
        "Rent": 18,
        "Services": 19,
    },
    "Life": {
        "Childcare": 20,
        "Clothing": 21,
        "Education": 22,
        "Gifts": 23,
        "Insurance": 24,
        "Medical Expenses": 25,
        "Taxes": 26,
    },
    "Transportation": {
        "Transportation": 27,
        "Bicycle": 28,
        "Bus/Train": 29,
        "Car": 30,
        "Gas/Fuel": 31,
        "Hotel": 32,
        "Parking": 33,
        "Plane": 34,
        "Taxi": 35,
    },
    "Utilities": {
        "Utilities": 36,
        "Cleaning": 37,
        "Electricity": 38,
        "Heat/Gas": 39,
        "Trash": 40,
        "TV/Phone/Internet": 41,
        "Water": 42,
    },
}

CATEGORIES: Tuple[Category, ...] = tuple(
    Category(id=str(category_id), name=name)
    for leaf_categories in _CATEGORY_GROUPS.values()
    for name, category_id in leaf_categories.items()
)


class SpliitExpenseBackend(ExpenseBackend):
    """
    Real ExpenseBackend implementation against Spliit's hosted instance
    (spliit.app), via the vendored `SpliitClient` (see ADR 0002's
    Amendment for why this isn't a PyPI dependency).
    """

    def __init__(self, group_ids: Iterable[str]) -> None:
        self._group_ids = list(group_ids)

    def _fetch_group(self, group_id: str) -> Group:
        raw = SpliitClient(group_id=group_id).get_group()
        return Group(
            id=group_id,
            name=raw["name"],
            participants=tuple(
                Participant(id=p["id"], name=p["name"])
                for p in raw["participants"]
            ),
        )

    def list_groups(self) -> List[Group]:
        return [self._fetch_group(group_id) for group_id in self._group_ids]

    def list_participants(self, group_id: str) -> List[Participant]:
        return list(self._fetch_group(group_id).participants)

    def list_categories(self) -> List[Category]:
        return list(CATEGORIES)

    def create_expense(self, expense: Expense) -> None:
        client = SpliitClient(group_id=expense.group_id)
        category = (
            int(expense.category_id) if expense.category_id is not None else 0
        )

        if expense.split is None:
            client.add_expense(
                title=expense.description,
                paid_by=expense.payer_id,
                paid_for=[expense.payer_id],
                amount=_to_cents(expense.amount),
                category=category,
            )
            return

        client.add_expense(
            title=expense.description,
            paid_by=expense.payer_id,
            paid_for=[
                (share.participant_id, _to_cents(share.owed_amount))
                for share in expense.split.shares
            ],
            amount=_to_cents(expense.amount),
            category=category,
            split_mode=SplitMode.BY_AMOUNT,
        )


def _to_cents(amount: Decimal) -> int:
    return int((amount * 100).to_integral_value())
