import pytest

from src.main.upload_expenses import UploadExpense


@pytest.fixture
def upload_expense_class():
    """
    Returns a UploadExpense class instance with filepath
    """
    return UploadExpense("src/tests/data/clean/test_data_raw_clean.csv")


@pytest.fixture
def user_id():
    """
    Returns the user id
    """
    return 23450949


@pytest.fixture
def user_friends():
    """
    Returns a dictionary of user's friends' ids and their first names.
    """
    return {
        82514972: "Tom",
        25087341: "Linda",
        39083412: "George",
    }


@pytest.fixture
def user_groups():
    """
    Returns a dictionary of user groups ids and group names.
    """
    return {
        0: "Non-group expenses",
        34894512: "Restaurant",
        20340193: "Home",
        12349123: "Travel",
        12035391: "Personal",
    }


@pytest.fixture
def user_groups_members():
    """
    Returns a dictionary of user group ids and a list of members id.
    """
    return {
        0: [23450949],
        34894512: [23450949, 82514972],
        20340193: [23450949, 82514972, 25087341],
        12349123: [23450949, 82514972, 39083412],
        12035391: [23450949],
    }


@pytest.mark.parametrize(
    "user_input, expected_result",
    [(("", 4), 12035391), (("", "a", 4), 12035391), (("", 3, 4), 12035391)],
)
def test_choose_personal_expense_group(
    upload_expense_class,
    user_groups,
    user_groups_members,
    user_id,
    monkeypatch,
    user_input,
    expected_result,
):
    inputs = iter(user_input)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert (
        upload_expense_class.choose_personal_expense_group(
            user_groups, user_groups_members, user_id
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "user_input, expected_result",
    [(" ", None), ("s", None), ("4", None), (" ", None)],
)
def test_choose_personal_expense_group_no_group(
    upload_expense_class,
    user_groups,
    user_groups_members,
    user_id,
    monkeypatch,
    user_input,
    expected_result,
):

    inputs = iter(user_input)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert (
        upload_expense_class.choose_personal_expense_group(
            user_groups, user_groups_members, user_id
        )
        is expected_result
    )


@pytest.mark.parametrize(
    "user_input_groups, personal_expense_group_id, expected_result",
    [
        ("1", 12035391, ("Restaurant", 34894512)),
        (("0", "1"), 12035391, ("Restaurant", 34894512)),
        ("4", 12035391, ("Personal", 12035391)),
        (("s", "4"), 12035391, ("Personal", 12035391)),
        (("6", "4"), 12035391, ("Personal", 12035391)),
        (("4", "2"), None, ("Home", 20340193)),
        (("0", "-2", "2"), None, ("Home", 20340193)),
    ],
)
def test_choose_group(
    upload_expense_class,
    user_groups,
    user_groups_members,
    user_input_groups,
    personal_expense_group_id,
    expected_result,
    monkeypatch,
):
    inputs = iter(user_input_groups)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert (
        upload_expense_class.choose_group(
            personal_expense_group_id, user_groups, user_groups_members
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "group_id, user_input_friends, expected_result",
    [
        (20340193, "1", ("Tom", 82514972)),
        (20340193, ("0", "2"), ("Linda", 25087341)),
        (12349123, ("0", "-1", "2"), ("George", 39083412)),
    ],
)
def test_choose_friend(
    upload_expense_class,
    user_groups_members,
    user_id,
    user_friends,
    group_id,
    user_input_friends,
    expected_result,
    monkeypatch,
):
    inputs = iter(user_input_friends)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert (
        upload_expense_class.choose_friend(
            group_id, user_groups_members, user_id, user_friends
        )
        == expected_result
    )
