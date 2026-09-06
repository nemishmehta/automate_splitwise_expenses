from datetime import date
from decimal import Decimal

import pytest

from src.core.fake_backend import FakeExpenseBackend
from src.core.models import (
    Category,
    Expense,
    Group,
    Participant,
    Share,
    Split,
    SplitMethod,
)


@pytest.fixture
def alice():
    return Participant(id="p1", name="Alice")


@pytest.fixture
def bob():
    return Participant(id="p2", name="Bob")


@pytest.fixture
def group(alice, bob):
    return Group(id="g1", name="Roommates", participants=(alice, bob))


@pytest.fixture
def backend(group):
    return FakeExpenseBackend(
        groups=[group],
        categories=[Category(id="cat-food", name="Food and drink")],
    )


def test_list_groups_returns_seeded_groups(backend, group):
    assert backend.list_groups() == [group]


def test_list_participants_returns_a_groups_participants(backend, alice, bob):
    assert backend.list_participants("g1") == [alice, bob]


def test_list_categories_returns_seeded_categories(backend):
    assert backend.list_categories() == [
        Category(id="cat-food", name="Food and drink")
    ]


def test_create_expense_records_the_expense_and_split_payload(backend):
    split = Split(
        method=SplitMethod.EQUAL,
        shares=(
            Share(participant_id="p1", owed_amount=Decimal("5")),
            Share(participant_id="p2", owed_amount=Decimal("5")),
        ),
    )
    expense = Expense(
        group_id="g1",
        description="Dinner",
        amount=Decimal("10"),
        currency="EUR",
        date=date(2026, 1, 15),
        payer_id="p1",
        category_id="cat-food",
        split=split,
    )

    backend.create_expense(expense)

    assert backend.created_expenses == [expense]
    assert backend.created_expenses[0].split.shares[1].owed_amount == (
        Decimal("5")
    )
