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


@pytest.mark.parametrize("val_list", [("", 4), ("", "a", 4), ("", 3, 4)])
def test_choose_personal_expense_group(
    upload_expense_class,
    user_groups,
    user_groups_members,
    user_id,
    monkeypatch,
    val_list,
):
    inputs = iter(val_list)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert (
        upload_expense_class.choose_personal_expense_group(
            user_groups, user_groups_members, user_id
        )
        == 12035391
    )


@pytest.mark.parametrize("val_list", [" ", "s", "4", " "])
def test_choose_personal_expense_group_no_group(
    upload_expense_class,
    user_groups,
    user_groups_members,
    user_id,
    monkeypatch,
    val_list,
):

    inputs = iter(val_list)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert (
        upload_expense_class.choose_personal_expense_group(
            user_groups, user_groups_members, user_id
        )
        is None
    )
