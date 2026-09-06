from datetime import date
from decimal import Decimal

from src.core.fake_backend import FakeExpenseBackend
from src.core.models import Group, Participant
from src.main.expense_cli import PersonalExpenseCLI

PARTICIPANT = Participant(id="p1", name="Nemish")
GROUP = Group(id="g1", name="Personal", participants=(PARTICIPANT,))


def _write_csv(tmp_path, rows):
    lines = ["date;amount;description;currency"]
    lines.extend(rows)
    path = tmp_path / "transactions_clean.csv"
    path.write_text("\n".join(lines) + "\n")
    return path


def _make_cli(csv_path, inputs, backend=None):
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
