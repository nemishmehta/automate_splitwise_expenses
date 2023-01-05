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


@pytest.fixture
def categories():
    """
    Returns a dictionary of available category names and their ids.
    """
    return {
        "Utilities": 1,
        "Uncategorized": 2,
        "Entertainment": 19,
        "Food and drink": 25,
    }


@pytest.fixture
def sub_categories():
    """
    Returns a dictionary of dictionaries of sub-category names and their
    Splitwise objects for each category.
    """
    return {
        "Utilities": {
            "Cleaning": "<splitwise.category.Category object at 0x104bfb940>",
            "Electricity": "<splitwise.category.Category object at 0x104bfb4>",
            "Heat/gas": "<splitwise.category.Category object at 0x104bfb8e0>",
        },
        "Uncategorized": {
            "General": "<splitwise.category.Category object at 0x104bfbb20>"
        },
        "Entertainment": {
            "Games": "<splitwise.category.Category object at 0x104bfb850>",
            "Movies": "<splitwise.category.Category object at 0x104bfb520>",
        },
        "Food and drink": {
            "Dining out": "<splitwise.category.Category object at 0x104bfb9a>",
            "Groceries": "<splitwise.category.Category object at 0x104bfba90>",
        },
    }


def iter_values(user_inputs, monkeypatch):
    inputs = iter(user_inputs)
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))


@pytest.mark.parametrize(
    "user_input, expected_result",
    [(["", 4], 12035391), (["", "a", 4], 12035391), (["", 3, 4], 12035391)],
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
    iter_values(user_input, monkeypatch)
    assert (
        upload_expense_class.choose_personal_expense_group(
            user_groups, user_groups_members, user_id
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "user_input, expected_result",
    [([" "], None), (["s"], None), (["4"], None), (["a"], None)],
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

    iter_values(user_input, monkeypatch)
    assert (
        upload_expense_class.choose_personal_expense_group(
            user_groups, user_groups_members, user_id
        )
        is expected_result
    )


@pytest.mark.parametrize(
    "user_input_groups, personal_expense_group_id, expected_result",
    [
        (["1"], 12035391, ("Restaurant", 34894512)),
        (["0", "1"], 12035391, ("Restaurant", 34894512)),
        (["4"], 12035391, ("Personal", 12035391)),
        (["s", "4"], 12035391, ("Personal", 12035391)),
        (["6", "4"], 12035391, ("Personal", 12035391)),
        (["4", "2"], None, ("Home", 20340193)),
        (["0", "-2", "2"], None, ("Home", 20340193)),
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
    iter_values(user_input_groups, monkeypatch)
    assert (
        upload_expense_class.choose_group(
            personal_expense_group_id, user_groups, user_groups_members
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "group_id, user_input_friends, expected_result",
    [
        (20340193, ["1"], ("Tom", 82514972)),
        (20340193, ["0", "2"], ("Linda", 25087341)),
        (12349123, ["0", "-1", "2"], ("George", 39083412)),
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
    iter_values(user_input_friends, monkeypatch)
    assert (
        upload_expense_class.choose_friend(
            group_id, user_groups_members, user_id, user_friends
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "chosen_category, user_input_sub_category, expected_result",
    [
        (
            "Entertainment",
            ["0"],
            ("Games", "<splitwise.category.Category object at 0x104bfb850>"),
        ),
        (
            "Entertainment",
            ["-1", "0"],
            ("Games", "<splitwise.category.Category object at 0x104bfb850>"),
        ),
    ],
)
def test_choose_sub_category(
    upload_expense_class,
    sub_categories,
    chosen_category,
    user_input_sub_category,
    expected_result,
    monkeypatch,
):
    iter_values(user_input_sub_category, monkeypatch)
    assert (
        upload_expense_class.choose_sub_category(
            sub_categories, chosen_category
        )
        == expected_result
    )


@pytest.mark.parametrize(
    "user_input_category, expected_result",
    [
        (["0"], "Utilities"),
        (["5", "2"], "Entertainment"),
        (["a", "2"], "Entertainment"),
    ],
)
def test_choose_category(
    upload_expense_class,
    categories,
    user_input_category,
    expected_result,
    monkeypatch,
):
    iter_values(user_input_category, monkeypatch)
    assert upload_expense_class.choose_category(categories) == expected_result


@pytest.mark.parametrize(
    "user_input_split_type, expected_result", [(["="], "="), (["|", "+"], "+")]
)
def test_choose_split_type(
    upload_expense_class, user_input_split_type, expected_result, monkeypatch
):
    iter_values(user_input_split_type, monkeypatch)
    assert upload_expense_class.choose_split_type() == expected_result


@pytest.mark.parametrize(
    "total_expense, expected_result",
    [(22.00, ("11.0", "11.0")), (33.33, ("16.66", "16.67"))],
)
def test_split_equally(upload_expense_class, total_expense, expected_result):
    assert upload_expense_class.split_equally(total_expense) == expected_result


@pytest.mark.parametrize(
    "total_expense, user_input_amount, expected_result",
    [
        (20, ["9"], ("11.0", "9.0")),
        (15.55, ["s", "10.5"], ("5.05", "10.5")),
        (10, ["5..3", "5.3"], ("4.7", "5.3")),
        (10, ["0", "5"], ("5.0", "5.0")),
        (10, ["12", "6"], ("4.0", "6.0")),
    ],
)
def test_split_by_exact_amount(
    upload_expense_class,
    total_expense,
    user_input_amount,
    expected_result,
    monkeypatch,
):
    iter_values(user_input_amount, monkeypatch)
    assert (
        upload_expense_class.split_by_exact_amount(total_expense)
        == expected_result
    )


@pytest.mark.parametrize(
    "total_expense, user_input_percent, expected_result",
    [
        (100, ["40"], ("60.0", "40.0")),
        (50, ["as", "20.54324"], ("39.73", "10.27")),
    ],
)
def test_split_by_percentage(
    upload_expense_class,
    total_expense,
    user_input_percent,
    expected_result,
    monkeypatch,
):
    iter_values(user_input_percent, monkeypatch)
    assert (
        upload_expense_class.split_by_percentage(total_expense)
        == expected_result
    )
