from src.core.category_suggestion import (
    CategorySuggestionHistory,
    KeywordRule,
    load_keyword_rules,
    suggest_category,
)


def test_suggest_returns_none_when_no_history_or_rules_match():
    suggestion = suggest_category(
        "Some unseen merchant",
        history={},
        keyword_rules=[],
    )

    assert suggestion is None


def test_suggest_returns_prior_history_choice_for_exact_description():
    suggestion = suggest_category(
        "Trader Joe's",
        history={"Trader Joe's": "cat-groceries"},
        keyword_rules=[],
    )

    assert suggestion == "cat-groceries"


def test_suggest_falls_back_to_keyword_rule_when_no_history_match():
    suggestion = suggest_category(
        "UBER *TRIP 8342",
        history={},
        keyword_rules=[
            KeywordRule(keyword="uber", category_id="cat-transport")
        ],
    )

    assert suggestion == "cat-transport"


def test_history_match_takes_priority_over_a_matching_keyword_rule():
    suggestion = suggest_category(
        "UBER *TRIP 8342",
        history={"UBER *TRIP 8342": "cat-business"},
        keyword_rules=[
            KeywordRule(keyword="uber", category_id="cat-transport")
        ],
    )

    assert suggestion == "cat-business"


def test_first_matching_keyword_rule_wins_when_several_match():
    suggestion = suggest_category(
        "UBER EATS DELIVERY",
        history={},
        keyword_rules=[
            KeywordRule(keyword="uber eats", category_id="cat-food"),
            KeywordRule(keyword="uber", category_id="cat-transport"),
        ],
    )

    assert suggestion == "cat-food"


def test_history_returns_none_for_a_description_with_no_recorded_choice(
    tmp_path,
):
    history = CategorySuggestionHistory(tmp_path / "history.json")

    assert history.get("Trader Joe's") is None


def test_history_returns_a_recorded_choice(tmp_path):
    history = CategorySuggestionHistory(tmp_path / "history.json")

    history.record("Trader Joe's", "cat-groceries")

    assert history.get("Trader Joe's") == "cat-groceries"


def test_history_persists_a_recorded_choice_across_instances(tmp_path):
    path = tmp_path / "history.json"
    CategorySuggestionHistory(path).record("Trader Joe's", "cat-groceries")

    reloaded = CategorySuggestionHistory(path)

    assert reloaded.get("Trader Joe's") == "cat-groceries"


def test_recording_a_new_choice_overrides_the_previous_one(tmp_path):
    history = CategorySuggestionHistory(tmp_path / "history.json")
    history.record("Trader Joe's", "cat-groceries")

    history.record("Trader Joe's", "cat-household")

    assert history.get("Trader Joe's") == "cat-household"


def test_load_keyword_rules_returns_empty_list_when_file_is_missing(
    tmp_path,
):
    assert load_keyword_rules(tmp_path / "missing.json") == []


def test_load_keyword_rules_reads_entries_from_a_json_file(tmp_path):
    path = tmp_path / "keyword_rules.json"
    path.write_text(
        '[{"keyword": "uber", "category_id": "cat-transport"}, '
        '{"keyword": "trader joe", "category_id": "cat-groceries"}]'
    )

    rules = load_keyword_rules(path)

    assert rules == [
        KeywordRule(keyword="uber", category_id="cat-transport"),
        KeywordRule(keyword="trader joe", category_id="cat-groceries"),
    ]


def test_suggest_accepts_a_category_suggestion_history_directly(tmp_path):
    history = CategorySuggestionHistory(tmp_path / "history.json")
    history.record("Trader Joe's", "cat-groceries")

    suggestion = suggest_category(
        "Trader Joe's",
        history=history,
        keyword_rules=[],
    )

    assert suggestion == "cat-groceries"
