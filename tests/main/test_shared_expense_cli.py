from datetime import date
from decimal import Decimal

from src.core.fake_backend import FakeExpenseBackend
from src.core.models import Group, Participant, SplitMethod
from src.main.expense_cli import SharedExpenseCLI

PAYER = Participant(id="p1", name="Nemish")
FRIEND_A = Participant(id="p2", name="Alice")
FRIEND_B = Participant(id="p3", name="Bob")
PERSONAL_GROUP = Group(id="g1", name="Personal", participants=(PAYER,))
SHARED_GROUP = Group(
    id="g2", name="Trip", participants=(PAYER, FRIEND_A, FRIEND_B)
)


def _write_csv(tmp_path, rows):
    lines = ["date;amount;description;currency"]
    lines.extend(rows)
    path = tmp_path / "transactions_clean.csv"
    path.write_text("\n".join(lines) + "\n")
    return path


def _make_cli(csv_path, inputs, backend=None, payer_ids=None):
    printed = []
    fed_inputs = iter(inputs)
    cli = SharedExpenseCLI(
        backend=backend
        or FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP]),
        payer_ids=payer_ids or {"g2": "p1"},
        csv_path=csv_path,
        input_fn=lambda _prompt: next(fed_inputs),
        print_fn=lambda *args, **kwargs: printed.append(
            " ".join(map(str, args))
        ),
    )
    return cli, printed


def test_submits_confirmed_transaction_as_shared_expense_with_equal_split(
    tmp_path,
):
    csv_path = _write_csv(tmp_path, ["30/12/2023;30.00;Dinner;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    # review, choose group 1 (Trip), choose both other participants, confirm
    cli, _ = _make_cli(csv_path, inputs=["", "1", "1,2", ""], backend=backend)

    cli.run()

    assert len(backend.created_expenses) == 1
    expense = backend.created_expenses[0]
    assert expense.group_id == "g2"
    assert expense.payer_id == "p1"
    assert expense.amount == Decimal("30.00")
    assert expense.date == date(2023, 12, 30)
    assert expense.split.method == SplitMethod.EQUAL
    shares = {
        share.participant_id: share.owed_amount
        for share in expense.split.shares
    }
    assert shares == {
        "p1": Decimal("10.00"),
        "p2": Decimal("10.00"),
        "p3": Decimal("10.00"),
    }


def test_equal_split_works_for_exactly_two_participants(tmp_path):
    csv_path = _write_csv(tmp_path, ["30/12/2023;20.00;Lunch;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    # review, choose group 1 (Trip), choose only participant 1 (Alice), confirm
    cli, _ = _make_cli(csv_path, inputs=["", "1", "1", ""], backend=backend)

    cli.run()

    expense = backend.created_expenses[0]
    shares = {
        share.participant_id: share.owed_amount
        for share in expense.split.shares
    }
    assert shares == {"p1": Decimal("10.00"), "p2": Decimal("10.00")}
    assert "p3" not in shares


def test_only_shared_groups_are_offered_as_choices(tmp_path):
    csv_path = _write_csv(tmp_path, ["30/12/2023;20.00;Lunch;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    cli, printed = _make_cli(
        csv_path, inputs=["", "1", "1,2", ""], backend=backend
    )

    cli.run()

    assert not any(PERSONAL_GROUP.name in line for line in printed)
    assert any(SHARED_GROUP.name in line for line in printed)
    assert backend.created_expenses[0].group_id == "g2"


def test_skips_transaction_without_prompting_for_group_or_participants(
    tmp_path,
):
    csv_path = _write_csv(tmp_path, ["30/12/2023;20.00;Lunch;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    cli, _ = _make_cli(csv_path, inputs=["skip"], backend=backend)

    cli.run()

    assert backend.created_expenses == []


def test_cancelling_at_confirmation_does_not_submit_the_expense(tmp_path):
    csv_path = _write_csv(tmp_path, ["30/12/2023;20.00;Lunch;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    cli, _ = _make_cli(
        csv_path, inputs=["", "1", "1,2", "cancel"], backend=backend
    )

    cli.run()

    assert backend.created_expenses == []


def test_prints_an_error_message_when_the_backend_raises(tmp_path):
    csv_path = _write_csv(tmp_path, ["30/12/2023;20.00;Lunch;EUR"])

    class FailingBackend(FakeExpenseBackend):
        def create_expense(self, expense):
            raise RuntimeError("boom")

    cli, printed = _make_cli(
        csv_path,
        inputs=["", "1", "1,2", ""],
        backend=FailingBackend(groups=[PERSONAL_GROUP, SHARED_GROUP]),
    )

    cli.run()

    assert any("boom" in line for line in printed)


def test_prints_a_summary_with_correct_counts(tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            "30/12/2023;20.00;First;EUR",
            "29/12/2023;30.00;Second;EUR",
        ],
    )
    cli, printed = _make_cli(
        csv_path, inputs=["", "1", "1,2", "", "skip"]
    )

    cli.run()

    summary_line = printed[-1]
    assert "1 submitted" in summary_line
    assert "1 skipped" in summary_line
    assert "0 failed" in summary_line
    assert "2 total" in summary_line
