from datetime import date
from decimal import Decimal

import pytest

from src.core.fake_backend import FakeExpenseBackend
from src.core.models import Expense, Group, Participant
from src.core.split import (
    compute_equal_split,
    compute_exact_split,
    compute_percentage_split,
)


def test_equal_split_divides_evenly_between_two_participants():
    split = compute_equal_split(
        participant_ids=["p1", "p2"],
        total=Decimal("10"),
        payer_id="p1",
    )

    amounts = {
        share.participant_id: share.owed_amount for share in split.shares
    }
    assert amounts == {"p1": Decimal("5"), "p2": Decimal("5")}


def test_equal_split_divides_evenly_among_three_participants():
    split = compute_equal_split(
        participant_ids=["p1", "p2", "p3"],
        total=Decimal("9"),
        payer_id="p1",
    )

    amounts = {
        share.participant_id: share.owed_amount for share in split.shares
    }
    assert amounts == {
        "p1": Decimal("3"),
        "p2": Decimal("3"),
        "p3": Decimal("3"),
    }


def test_equal_split_assigns_rounding_remainder_to_the_payer():
    split = compute_equal_split(
        participant_ids=["p1", "p2", "p3"],
        total=Decimal("10"),
        payer_id="p1",
    )

    amounts = {
        share.participant_id: share.owed_amount for share in split.shares
    }
    assert amounts == {
        "p1": Decimal("3.34"),
        "p2": Decimal("3.33"),
        "p3": Decimal("3.33"),
    }
    assert sum(amounts.values()) == Decimal("10")


def test_equal_split_rejects_fewer_than_two_participants():
    with pytest.raises(ValueError):
        compute_equal_split(
            participant_ids=["p1"],
            total=Decimal("10"),
            payer_id="p1",
        )


def test_equal_split_rejects_a_payer_not_among_the_participants():
    with pytest.raises(ValueError):
        compute_equal_split(
            participant_ids=["p1", "p2"],
            total=Decimal("10"),
            payer_id="p3",
        )


def test_expense_with_an_equal_split_is_submitted_through_the_adapter():
    alice = Participant(id="p1", name="Alice")
    bob = Participant(id="p2", name="Bob")
    carol = Participant(id="p3", name="Carol")
    group = Group(id="g1", name="Trip", participants=(alice, bob, carol))
    backend = FakeExpenseBackend(groups=[group])

    split = compute_equal_split(
        participant_ids=["p1", "p2", "p3"],
        total=Decimal("10"),
        payer_id="p1",
    )
    expense = Expense(
        group_id="g1",
        description="Dinner",
        amount=Decimal("10"),
        currency="EUR",
        date=date(2026, 1, 15),
        payer_id="p1",
        category_id=None,
        split=split,
    )

    backend.create_expense(expense)

    [submitted] = backend.created_expenses
    assert submitted.payer_id == "p1"
    submitted_amounts = {
        share.participant_id: share.owed_amount
        for share in submitted.split.shares
    }
    assert submitted_amounts == {
        "p1": Decimal("3.34"),
        "p2": Decimal("3.33"),
        "p3": Decimal("3.33"),
    }


def test_exact_split_uses_the_given_amounts_for_two_participants():
    split = compute_exact_split(
        amounts={"p1": Decimal("7"), "p2": Decimal("3")},
        total=Decimal("10"),
        payer_id="p1",
    )

    amounts = {
        share.participant_id: share.owed_amount for share in split.shares
    }
    assert amounts == {"p1": Decimal("7"), "p2": Decimal("3")}


def test_exact_split_uses_the_given_amounts_for_three_participants():
    split = compute_exact_split(
        amounts={
            "p1": Decimal("5"),
            "p2": Decimal("3"),
            "p3": Decimal("2"),
        },
        total=Decimal("10"),
        payer_id="p1",
    )

    amounts = {
        share.participant_id: share.owed_amount for share in split.shares
    }
    assert amounts == {
        "p1": Decimal("5"),
        "p2": Decimal("3"),
        "p3": Decimal("2"),
    }


def test_exact_split_rejects_amounts_that_dont_sum_to_the_total():
    with pytest.raises(ValueError):
        compute_exact_split(
            amounts={"p1": Decimal("7"), "p2": Decimal("2")},
            total=Decimal("10"),
            payer_id="p1",
        )


def test_exact_split_accepts_amounts_within_rounding_tolerance_of_the_total():
    split = compute_exact_split(
        amounts={"p1": Decimal("6.665"), "p2": Decimal("3.334")},
        total=Decimal("10"),
        payer_id="p1",
    )

    assert split is not None


def test_exact_split_rejects_a_payer_not_among_the_amounts():
    with pytest.raises(ValueError):
        compute_exact_split(
            amounts={"p1": Decimal("5"), "p2": Decimal("5")},
            total=Decimal("10"),
            payer_id="p3",
        )


def test_expense_with_an_exact_split_is_submitted_through_the_adapter():
    alice = Participant(id="p1", name="Alice")
    bob = Participant(id="p2", name="Bob")
    carol = Participant(id="p3", name="Carol")
    group = Group(id="g1", name="Trip", participants=(alice, bob, carol))
    backend = FakeExpenseBackend(groups=[group])

    split = compute_exact_split(
        amounts={
            "p1": Decimal("5"),
            "p2": Decimal("3"),
            "p3": Decimal("2"),
        },
        total=Decimal("10"),
        payer_id="p1",
    )
    expense = Expense(
        group_id="g1",
        description="Dinner",
        amount=Decimal("10"),
        currency="EUR",
        date=date(2026, 1, 15),
        payer_id="p1",
        category_id=None,
        split=split,
    )

    backend.create_expense(expense)

    [submitted] = backend.created_expenses
    assert submitted.payer_id == "p1"
    submitted_amounts = {
        share.participant_id: share.owed_amount
        for share in submitted.split.shares
    }
    assert submitted_amounts == {
        "p1": Decimal("5"),
        "p2": Decimal("3"),
        "p3": Decimal("2"),
    }


def test_percentage_split_divides_the_total_for_two_participants():
    split = compute_percentage_split(
        percentages={"p1": Decimal("70"), "p2": Decimal("30")},
        total=Decimal("10"),
        payer_id="p1",
    )

    amounts = {
        share.participant_id: share.owed_amount for share in split.shares
    }
    assert amounts == {"p1": Decimal("7"), "p2": Decimal("3")}


def test_percentage_split_divides_the_total_for_three_participants():
    split = compute_percentage_split(
        percentages={
            "p1": Decimal("50"),
            "p2": Decimal("25"),
            "p3": Decimal("25"),
        },
        total=Decimal("10"),
        payer_id="p1",
    )

    amounts = {
        share.participant_id: share.owed_amount for share in split.shares
    }
    assert amounts == {
        "p1": Decimal("5"),
        "p2": Decimal("2.50"),
        "p3": Decimal("2.50"),
    }


def test_percentage_split_assigns_rounding_remainder_to_the_payer():
    split = compute_percentage_split(
        percentages={
            "p1": Decimal("34"),
            "p2": Decimal("33"),
            "p3": Decimal("33"),
        },
        total=Decimal("10"),
        payer_id="p1",
    )

    amounts = {
        share.participant_id: share.owed_amount for share in split.shares
    }
    assert amounts == {
        "p1": Decimal("3.40"),
        "p2": Decimal("3.30"),
        "p3": Decimal("3.30"),
    }
    assert sum(amounts.values()) == Decimal("10")


def test_percentage_split_rejects_percentages_that_dont_sum_to_100():
    with pytest.raises(ValueError):
        compute_percentage_split(
            percentages={"p1": Decimal("70"), "p2": Decimal("20")},
            total=Decimal("10"),
            payer_id="p1",
        )


def test_percentage_split_accepts_percentages_within_rounding_tolerance():
    split = compute_percentage_split(
        percentages={"p1": Decimal("70.005"), "p2": Decimal("29.99")},
        total=Decimal("10"),
        payer_id="p1",
    )

    assert split is not None


def test_percentage_split_rejects_a_payer_not_among_the_percentages():
    with pytest.raises(ValueError):
        compute_percentage_split(
            percentages={"p1": Decimal("50"), "p2": Decimal("50")},
            total=Decimal("10"),
            payer_id="p3",
        )


def test_expense_with_a_percentage_split_is_submitted_through_the_adapter():
    alice = Participant(id="p1", name="Alice")
    bob = Participant(id="p2", name="Bob")
    group = Group(id="g1", name="Flatmates", participants=(alice, bob))
    backend = FakeExpenseBackend(groups=[group])

    split = compute_percentage_split(
        percentages={"p1": Decimal("70"), "p2": Decimal("30")},
        total=Decimal("10"),
        payer_id="p1",
    )
    expense = Expense(
        group_id="g1",
        description="Rent top-up",
        amount=Decimal("10"),
        currency="EUR",
        date=date(2026, 1, 15),
        payer_id="p1",
        category_id=None,
        split=split,
    )

    backend.create_expense(expense)

    [submitted] = backend.created_expenses
    assert submitted.payer_id == "p1"
    submitted_amounts = {
        share.participant_id: share.owed_amount
        for share in submitted.split.shares
    }
    assert submitted_amounts == {"p1": Decimal("7"), "p2": Decimal("3")}
