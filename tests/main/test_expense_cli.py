from datetime import date
from decimal import Decimal

from src.core.category_suggestion import CategorySuggestionHistory, KeywordRule
from src.core.fake_backend import FakeExpenseBackend
from src.core.models import Category, Group, Participant
from src.main.expense_cli import PersonalExpenseCLI

PARTICIPANT = Participant(id="p1", name="Nemish")
GROUP = Group(id="g1", name="Personal", participants=(PARTICIPANT,))
FOOD = Category(id="cat-food", name="Food and drink")
TRANSPORT = Category(id="cat-transport", name="Transportation")


def _write_csv(tmp_path, rows):
    lines = ["date;amount;description;currency"]
    lines.extend(rows)
    path = tmp_path / "transactions_clean.csv"
    path.write_text("\n".join(lines) + "\n")
    return path


def _make_cli(
    csv_path,
    inputs,
    backend=None,
    category_suggestions=None,
    keyword_rules=None,
):
    printed = []
    fed_inputs = iter(inputs)
    cli = PersonalExpenseCLI(
        backend=backend or FakeExpenseBackend(groups=[GROUP]),
        group_id=GROUP.id,
        csv_path=csv_path,
        input_fn=lambda _prompt: next(fed_inputs),
        print_fn=lambda *args, **kwargs: printed.append(
            " ".join(map(str, args))
        ),
        category_suggestions=category_suggestions,
        keyword_rules=keyword_rules,
    )
    return cli, printed


def test_submits_confirmed_transaction_as_personal_expense(tmp_path):
    csv_path = _write_csv(
        tmp_path, ["30/12/2023;38.50;PELE MELE XL Ixelles to:;EUR"]
    )
    backend = FakeExpenseBackend(groups=[GROUP])
    cli, _ = _make_cli(csv_path, inputs=["", ""], backend=backend)

    cli.run()

    assert len(backend.created_expenses) == 1
    expense = backend.created_expenses[0]
    assert expense.group_id == "g1"
    assert expense.payer_id == "p1"
    assert expense.amount == Decimal("38.50")
    assert expense.description == "PELE MELE XL Ixelles to:"
    assert expense.currency == "EUR"
    assert expense.date == date(2023, 12, 30)
    assert expense.category_id is None
    assert expense.split is None


def test_skips_transaction_without_prompting_for_confirmation(tmp_path):
    csv_path = _write_csv(
        tmp_path, ["30/12/2023;38.50;PELE MELE XL Ixelles to:;EUR"]
    )
    backend = FakeExpenseBackend(groups=[GROUP])
    cli, _ = _make_cli(csv_path, inputs=["skip"], backend=backend)

    cli.run()

    assert backend.created_expenses == []


def test_cancelling_at_confirmation_does_not_submit_the_expense(tmp_path):
    csv_path = _write_csv(
        tmp_path, ["30/12/2023;38.50;PELE MELE XL Ixelles to:;EUR"]
    )
    backend = FakeExpenseBackend(groups=[GROUP])
    cli, _ = _make_cli(csv_path, inputs=["", "cancel"], backend=backend)

    cli.run()

    assert backend.created_expenses == []


def test_prints_a_success_message_after_submission(tmp_path):
    csv_path = _write_csv(
        tmp_path, ["30/12/2023;38.50;PELE MELE XL Ixelles to:;EUR"]
    )
    cli, printed = _make_cli(csv_path, inputs=["", ""])

    cli.run()

    assert any("success" in line.lower() for line in printed)


def test_prints_an_error_message_when_the_backend_raises(tmp_path):
    csv_path = _write_csv(
        tmp_path, ["30/12/2023;38.50;PELE MELE XL Ixelles to:;EUR"]
    )

    class FailingBackend(FakeExpenseBackend):
        def create_expense(self, expense):
            raise RuntimeError("boom")

    cli, printed = _make_cli(
        csv_path, inputs=["", ""], backend=FailingBackend(groups=[GROUP])
    )

    cli.run()

    assert any("boom" in line for line in printed)


def test_a_suggested_category_is_prefilled_and_confirmed_with_enter(
    tmp_path,
):
    csv_path = _write_csv(
        tmp_path, ["30/12/2023;38.50;PELE MELE XL Ixelles to:;EUR"]
    )
    history = CategorySuggestionHistory(tmp_path / "history.json")
    history.record("PELE MELE XL Ixelles to:", FOOD.id)
    backend = FakeExpenseBackend(groups=[GROUP], categories=[FOOD])
    # review, accept suggested Category, confirm
    cli, printed = _make_cli(
        csv_path,
        inputs=["", "", ""],
        backend=backend,
        category_suggestions=history,
    )

    cli.run()

    expense = backend.created_expenses[0]
    assert expense.category_id == FOOD.id
    assert any("Food and drink" in line for line in printed)


def test_declining_a_suggested_category_prompts_for_a_manual_choice_and_overrides_history(  # noqa: E501
    tmp_path,
):
    csv_path = _write_csv(
        tmp_path, ["30/12/2023;38.50;PELE MELE XL Ixelles to:;EUR"]
    )
    history = CategorySuggestionHistory(tmp_path / "history.json")
    history.record("PELE MELE XL Ixelles to:", FOOD.id)
    backend = FakeExpenseBackend(groups=[GROUP], categories=[FOOD, TRANSPORT])
    # review, decline suggested Category, choose Transportation (2), confirm
    cli, _ = _make_cli(
        csv_path,
        inputs=["", "no", "2", ""],
        backend=backend,
        category_suggestions=history,
    )

    cli.run()

    expense = backend.created_expenses[0]
    assert expense.category_id == TRANSPORT.id
    assert history.get("PELE MELE XL Ixelles to:") == TRANSPORT.id


def test_no_suggestion_falls_through_to_a_manual_category_choice(tmp_path):
    csv_path = _write_csv(tmp_path, ["30/12/2023;38.50;Some new merchant;EUR"])
    history = CategorySuggestionHistory(tmp_path / "history.json")
    backend = FakeExpenseBackend(groups=[GROUP], categories=[FOOD, TRANSPORT])
    # review, choose Food and drink (1), confirm
    cli, _ = _make_cli(
        csv_path,
        inputs=["", "1", ""],
        backend=backend,
        category_suggestions=history,
    )

    cli.run()

    expense = backend.created_expenses[0]
    assert expense.category_id == FOOD.id
    assert history.get("Some new merchant") == FOOD.id


def test_choosing_none_as_the_category_leaves_it_unset(tmp_path):
    csv_path = _write_csv(tmp_path, ["30/12/2023;38.50;Some new merchant;EUR"])
    backend = FakeExpenseBackend(groups=[GROUP], categories=[FOOD])
    # review, choose 0 (None), confirm
    cli, _ = _make_cli(csv_path, inputs=["", "0", ""], backend=backend)

    cli.run()

    expense = backend.created_expenses[0]
    assert expense.category_id is None


def test_keyword_rule_suggests_a_category_for_a_never_seen_description(
    tmp_path,
):
    csv_path = _write_csv(tmp_path, ["30/12/2023;12.00;Uber trip;EUR"])
    history = CategorySuggestionHistory(tmp_path / "history.json")
    backend = FakeExpenseBackend(groups=[GROUP], categories=[FOOD, TRANSPORT])
    # review, accept suggested Category, confirm
    cli, _ = _make_cli(
        csv_path,
        inputs=["", "", ""],
        backend=backend,
        category_suggestions=history,
        keyword_rules=[KeywordRule(keyword="uber", category_id=TRANSPORT.id)],
    )

    cli.run()

    expense = backend.created_expenses[0]
    assert expense.category_id == TRANSPORT.id


def test_prints_a_summary_with_correct_counts(tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            "30/12/2023;38.50;First;EUR",
            "29/12/2023;47.70;Second;EUR",
        ],
    )
    cli, printed = _make_cli(csv_path, inputs=["", "", "skip"])

    cli.run()

    summary_line = printed[-1]
    assert "1 submitted" in summary_line
    assert "1 skipped" in summary_line
    assert "0 failed" in summary_line
    assert "2 total" in summary_line
