from datetime import date
from decimal import Decimal

from src.core.category_suggestion import CategorySuggestionHistory
from src.core.default_split_profile import DefaultSplitProfileStore
from src.core.fake_backend import FakeExpenseBackend
from src.core.models import Category, Group, Participant, SplitMethod
from src.main.expense_cli import SharedExpenseCLI

PAYER = Participant(id="p1", name="Nemish")
FRIEND_A = Participant(id="p2", name="Alice")
FRIEND_B = Participant(id="p3", name="Bob")
PERSONAL_GROUP = Group(id="g1", name="Personal", participants=(PAYER,))
SHARED_GROUP = Group(
    id="g2", name="Trip", participants=(PAYER, FRIEND_A, FRIEND_B)
)
FOOD = Category(id="cat-food", name="Food and drink")


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
    payer_ids=None,
    default_split_profiles=None,
    category_suggestions=None,
):
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
        default_split_profiles=default_split_profiles,
        category_suggestions=category_suggestions,
    )
    return cli, printed


def test_submits_confirmed_transaction_as_shared_expense_with_equal_split(
    tmp_path,
):
    csv_path = _write_csv(tmp_path, ["30/12/2023;30.00;Dinner;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    # review, choose group 1 (Trip), choose both other participants,
    # choose split method 1 (Equal), confirm
    cli, _ = _make_cli(
        csv_path, inputs=["", "1", "1,2", "1", ""], backend=backend
    )

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
    # review, choose group 1 (Trip), choose only participant 1 (Alice),
    # choose split method 1 (Equal), confirm
    cli, _ = _make_cli(
        csv_path, inputs=["", "1", "1", "1", ""], backend=backend
    )

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
        csv_path, inputs=["", "1", "1,2", "1", ""], backend=backend
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
        csv_path, inputs=["", "1", "1,2", "1", "cancel"], backend=backend
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
        inputs=["", "1", "1,2", "1", ""],
        backend=FailingBackend(groups=[PERSONAL_GROUP, SHARED_GROUP]),
    )

    cli.run()

    assert any("boom" in line for line in printed)


def test_a_suggested_category_is_prefilled_and_confirmed_with_enter(
    tmp_path,
):
    csv_path = _write_csv(tmp_path, ["30/12/2023;30.00;Dinner;EUR"])
    history = CategorySuggestionHistory(tmp_path / "history.json")
    history.record("Dinner", FOOD.id)
    backend = FakeExpenseBackend(
        groups=[PERSONAL_GROUP, SHARED_GROUP], categories=[FOOD]
    )
    # review, group 1, both others, Equal, accept suggested Category,
    # confirm
    cli, _ = _make_cli(
        csv_path,
        inputs=["", "1", "1,2", "1", "", ""],
        backend=backend,
        category_suggestions=history,
    )

    cli.run()

    expense = backend.created_expenses[0]
    assert expense.category_id == FOOD.id


def test_submits_shared_expense_with_exact_amount_split(tmp_path):
    csv_path = _write_csv(tmp_path, ["30/12/2023;30.00;Dinner;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    # review, choose group 1 (Trip), choose both other participants,
    # choose split method 2 (Exact Amount), enter amounts for p1,p2,p3,
    # confirm
    cli, _ = _make_cli(
        csv_path,
        inputs=["", "1", "1,2", "2", "5,10,15", ""],
        backend=backend,
    )

    cli.run()

    expense = backend.created_expenses[0]
    assert expense.split.method == SplitMethod.EXACT
    shares = {
        share.participant_id: share.owed_amount
        for share in expense.split.shares
    }
    assert shares == {
        "p1": Decimal("5"),
        "p2": Decimal("10"),
        "p3": Decimal("15"),
    }


def test_exact_amount_split_reprompts_when_amounts_do_not_sum_to_total(
    tmp_path,
):
    csv_path = _write_csv(tmp_path, ["30/12/2023;30.00;Dinner;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    cli, printed = _make_cli(
        csv_path,
        # first attempt sums to 25, not 30 - should be rejected and
        # re-prompted before the valid second attempt is accepted
        inputs=["", "1", "1,2", "2", "5,10,10", "5,10,15", ""],
        backend=backend,
    )

    cli.run()

    assert len(backend.created_expenses) == 1
    shares = {
        share.participant_id: share.owed_amount
        for share in backend.created_expenses[0].split.shares
    }
    assert shares == {
        "p1": Decimal("5"),
        "p2": Decimal("10"),
        "p3": Decimal("15"),
    }
    assert any("must sum to" in line for line in printed)


def test_submits_shared_expense_with_percentage_split(tmp_path):
    csv_path = _write_csv(tmp_path, ["30/12/2023;30.00;Dinner;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    # review, choose group 1 (Trip), choose both other participants,
    # choose split method 3 (Percentage), enter percentages for p1,p2,p3,
    # confirm
    cli, _ = _make_cli(
        csv_path,
        inputs=["", "1", "1,2", "3", "50,25,25", ""],
        backend=backend,
    )

    cli.run()

    expense = backend.created_expenses[0]
    assert expense.split.method == SplitMethod.PERCENTAGE
    shares = {
        share.participant_id: share.owed_amount
        for share in expense.split.shares
    }
    assert shares == {
        "p1": Decimal("15.00"),
        "p2": Decimal("7.50"),
        "p3": Decimal("7.50"),
    }


def test_percentage_split_reprompts_when_percentages_do_not_sum_to_100(
    tmp_path,
):
    csv_path = _write_csv(tmp_path, ["30/12/2023;30.00;Dinner;EUR"])
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    cli, printed = _make_cli(
        csv_path,
        # first attempt sums to 90, not 100 - should be rejected and
        # re-prompted before the valid second attempt is accepted
        inputs=["", "1", "1,2", "3", "50,25,15", "50,25,25", ""],
        backend=backend,
    )

    cli.run()

    assert len(backend.created_expenses) == 1
    shares = {
        share.participant_id: share.owed_amount
        for share in backend.created_expenses[0].split.shares
    }
    assert shares == {
        "p1": Decimal("15.00"),
        "p2": Decimal("7.50"),
        "p3": Decimal("7.50"),
    }
    assert any("must sum to" in line for line in printed)


def test_first_use_of_a_participant_set_saves_a_default_split_profile(
    tmp_path,
):
    csv_path = _write_csv(tmp_path, ["30/12/2023;30.00;Dinner;EUR"])
    profiles = DefaultSplitProfileStore(tmp_path / "profiles.json")
    cli, _ = _make_cli(
        csv_path,
        inputs=["", "1", "1,2", "1", ""],
        default_split_profiles=profiles,
    )

    cli.run()

    profile = profiles.get(["p1", "p2", "p3"])
    assert profile is not None
    assert profile.method == SplitMethod.EQUAL
    assert profile.values is None


def test_a_saved_default_split_is_prefilled_and_confirmed_with_enter(
    tmp_path,
):
    csv_path = _write_csv(
        tmp_path,
        [
            "30/12/2023;30.00;Dinner;EUR",
            "29/12/2023;45.00;Groceries;EUR",
        ],
    )
    profiles = DefaultSplitProfileStore(tmp_path / "profiles.json")
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    # first transaction: review, group 1, both others, Percentage,
    # 50/25/25, confirm
    # second transaction: review, group 1, both others (same set, in a
    # different comma order), accept the pre-filled Default Split, confirm
    cli, _ = _make_cli(
        csv_path,
        inputs=[
            "",
            "1",
            "1,2",
            "3",
            "50,25,25",
            "",
            "",
            "1",
            "2,1",
            "",
            "",
        ],
        backend=backend,
        default_split_profiles=profiles,
    )

    cli.run()

    backend_created = backend.created_expenses
    assert len(backend_created) == 2
    second_expense = backend_created[1]
    assert second_expense.split.method == SplitMethod.PERCENTAGE
    shares = {
        share.participant_id: share.owed_amount
        for share in second_expense.split.shares
    }
    assert shares == {
        "p1": Decimal("22.50"),
        "p2": Decimal("11.25"),
        "p3": Decimal("11.25"),
    }


def test_declining_a_prefilled_default_falls_through_and_overrides_it(
    tmp_path,
):
    csv_path = _write_csv(
        tmp_path,
        [
            "30/12/2023;30.00;Dinner;EUR",
            "29/12/2023;40.00;Groceries;EUR",
            "28/12/2023;40.00;Taxi;EUR",
        ],
    )
    profiles = DefaultSplitProfileStore(tmp_path / "profiles.json")
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    # 1st: review, group 1, both others, Equal, confirm
    # 2nd: review, group 1, both others, decline default, Exact Amount,
    #      values, confirm
    # 3rd: review, group 1, both others, accept the (now-updated) default,
    #      confirm
    cli, _ = _make_cli(
        csv_path,
        inputs=[
            "",
            "1",
            "1,2",
            "1",
            "",
            "",
            "1",
            "1,2",
            "skip",
            "2",
            "10,10,20",
            "",
            "",
            "1",
            "1,2",
            "",
            "",
        ],
        backend=backend,
        default_split_profiles=profiles,
    )

    cli.run()

    backend_created = backend.created_expenses
    assert len(backend_created) == 3
    third_expense = backend_created[2]
    assert third_expense.split.method == SplitMethod.EXACT
    shares = {
        share.participant_id: share.owed_amount
        for share in third_expense.split.shares
    }
    assert shares == {
        "p1": Decimal("10"),
        "p2": Decimal("10"),
        "p3": Decimal("20"),
    }


def test_two_different_participant_sets_get_independent_default_splits(
    tmp_path,
):
    csv_path = _write_csv(
        tmp_path,
        [
            "30/12/2023;20.00;Lunch with Alice;EUR",
            "29/12/2023;30.00;Dinner with everyone;EUR",
            "28/12/2023;20.00;Coffee with Alice;EUR",
        ],
    )
    profiles = DefaultSplitProfileStore(tmp_path / "profiles.json")
    backend = FakeExpenseBackend(groups=[PERSONAL_GROUP, SHARED_GROUP])
    # 1st: {p1, p2} - Equal
    # 2nd: {p1, p2, p3} - Percentage 50/25/25
    # 3rd: {p1, p2} again - should offer the Equal default, not Percentage
    cli, printed = _make_cli(
        csv_path,
        inputs=[
            "",
            "1",
            "1",
            "1",
            "",
            "",
            "1",
            "1,2",
            "3",
            "50,25,25",
            "",
            "",
            "1",
            "1",
            "",
            "",
        ],
        backend=backend,
        default_split_profiles=profiles,
    )

    cli.run()

    backend_created = backend.created_expenses
    assert len(backend_created) == 3
    third_expense = backend_created[2]
    assert third_expense.split.method == SplitMethod.EQUAL
    assert any("Default Split found: equal" in line for line in printed)


def test_prints_a_summary_with_correct_counts(tmp_path):
    csv_path = _write_csv(
        tmp_path,
        [
            "30/12/2023;20.00;First;EUR",
            "29/12/2023;30.00;Second;EUR",
        ],
    )
    cli, printed = _make_cli(
        csv_path, inputs=["", "1", "1,2", "1", "", "skip"]
    )

    cli.run()

    summary_line = printed[-1]
    assert "1 submitted" in summary_line
    assert "1 skipped" in summary_line
    assert "0 failed" in summary_line
    assert "2 total" in summary_line
