from datetime import date
from decimal import Decimal

import pytest

from src.core.models import (
    Category,
    Expense,
    Group,
    Participant,
    Share,
    Split,
    SplitMethod,
)


def test_split_rejects_fewer_than_two_shares():
    with pytest.raises(ValueError):
        Split(
            method=SplitMethod.EQUAL,
            shares=(Share(participant_id="p1", owed_amount=Decimal("10")),),
        )


def test_split_accepts_two_or_more_shares():
    split = Split(
        method=SplitMethod.EQUAL,
        shares=(
            Share(participant_id="p1", owed_amount=Decimal("5")),
            Share(participant_id="p2", owed_amount=Decimal("5")),
            Share(participant_id="p3", owed_amount=Decimal("5")),
        ),
    )

    assert len(split.shares) == 3


def test_split_rejects_duplicate_participant():
    with pytest.raises(ValueError):
        Split(
            method=SplitMethod.EQUAL,
            shares=(
                Share(participant_id="p1", owed_amount=Decimal("5")),
                Share(participant_id="p1", owed_amount=Decimal("5")),
            ),
        )


def test_group_holds_its_participants():
    alice = Participant(id="p1", name="Alice")
    bob = Participant(id="p2", name="Bob")

    group = Group(id="g1", name="Roommates", participants=(alice, bob))

    assert group.participants == (alice, bob)


def test_personal_expense_has_a_single_participant_and_no_split():
    expense = Expense(
        group_id="g1",
        description="Coffee",
        amount=Decimal("4.50"),
        currency="EUR",
        date=date(2026, 1, 15),
        payer_id="p1",
        category_id=None,
        split=None,
    )

    assert expense.split is None
    assert expense.payer_id == "p1"


def test_shared_expense_carries_its_split():
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

    assert expense.split.shares[1].owed_amount == Decimal("5")


def test_category_has_id_and_name():
    category = Category(id="cat-food", name="Food and drink")

    assert category.name == "Food and drink"
