from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from src.core.models import Category, Expense, Group, Participant
from src.core.split import compute_equal_split
from src.spliit.backend import SpliitExpenseBackend
from src.spliit.client import SplitMode


def test_list_categories_returns_spliits_fixed_category_taxonomy():
    backend = SpliitExpenseBackend(group_ids=[])

    categories = backend.list_categories()

    assert Category(id="9", name="Groceries") in categories
    assert Category(id="0", name="General") in categories


def test_list_groups_fetches_each_configured_group_from_spliit():
    fake_group = {
        "name": "Trip",
        "participants": [
            {"id": "p1", "name": "Alice"},
            {"id": "p2", "name": "Bob"},
        ],
    }
    with patch("src.spliit.backend.SpliitClient") as MockClient:
        MockClient.return_value.get_group.return_value = fake_group
        backend = SpliitExpenseBackend(group_ids=["g1"])

        groups = backend.list_groups()

    MockClient.assert_called_once_with(group_id="g1")
    assert groups == [
        Group(
            id="g1",
            name="Trip",
            participants=(
                Participant(id="p1", name="Alice"),
                Participant(id="p2", name="Bob"),
            ),
        )
    ]


def test_list_groups_skips_a_group_that_fails_to_fetch_and_reports_it():
    good_group = {
        "name": "Trip",
        "participants": [{"id": "p1", "name": "Alice"}],
    }
    errors = []
    with patch("src.spliit.backend.SpliitClient") as MockClient:

        def fake_get_group(self):
            if self.group_id == "bad":
                raise RuntimeError("boom")
            return good_group

        MockClient.side_effect = lambda group_id: SimpleNamespace(
            get_group=lambda: fake_get_group(
                SimpleNamespace(group_id=group_id)
            )
        )
        backend = SpliitExpenseBackend(
            group_ids=["g1", "bad"],
            on_group_error=lambda group_id, exc: errors.append(
                (group_id, exc)
            ),
        )

        groups = backend.list_groups()

    assert [group.id for group in groups] == ["g1"]
    assert len(errors) == 1
    assert errors[0][0] == "bad"
    assert isinstance(errors[0][1], RuntimeError)


def test_list_participants_returns_the_groups_participants():
    fake_group = {
        "name": "Trip",
        "participants": [
            {"id": "p1", "name": "Alice"},
            {"id": "p2", "name": "Bob"},
        ],
    }
    with patch("src.spliit.backend.SpliitClient") as MockClient:
        MockClient.return_value.get_group.return_value = fake_group
        backend = SpliitExpenseBackend(group_ids=["g1"])

        participants = backend.list_participants("g1")

    assert participants == [
        Participant(id="p1", name="Alice"),
        Participant(id="p2", name="Bob"),
    ]


def test_create_expense_submits_a_personal_expense_as_an_even_split_of_one():
    expense = Expense(
        group_id="g1",
        description="Groceries",
        amount=Decimal("12.50"),
        currency="EUR",
        date=date(2026, 1, 15),
        payer_id="p1",
        category_id="9",
        split=None,
    )
    with patch("src.spliit.backend.SpliitClient") as MockClient:
        backend = SpliitExpenseBackend(group_ids=["g1"])

        backend.create_expense(expense)

    MockClient.assert_called_once_with(group_id="g1")
    MockClient.return_value.add_expense.assert_called_once_with(
        title="Groceries",
        paid_by="p1",
        paid_for=["p1"],
        amount=1250,
        category=9,
    )


def test_create_expense_submits_a_shared_expense_as_an_exact_by_amount_split():
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
    with patch("src.spliit.backend.SpliitClient") as MockClient:
        backend = SpliitExpenseBackend(group_ids=["g1"])

        backend.create_expense(expense)

    MockClient.return_value.add_expense.assert_called_once_with(
        title="Dinner",
        paid_by="p1",
        paid_for=[("p1", 334), ("p2", 333), ("p3", 333)],
        amount=1000,
        category=0,
        split_mode=SplitMode.BY_AMOUNT,
    )
