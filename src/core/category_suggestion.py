import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union


@dataclass(frozen=True)
class KeywordRule:
    """
    A user-defined fallback rule: a description containing `keyword`
    (case-insensitive) suggests `category_id` when no history match exists.
    """

    keyword: str
    category_id: str


class CategorySuggestionHistory:
    """
    Durable local storage of the owner's own description->Category choices,
    keyed by exact description text. Backed by a JSON file so choices
    persist across runs; recording a new choice for a description that
    already has one overrides it.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._choices: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return {}

    def get(self, description: str) -> Optional[str]:
        return self._choices.get(description)

    def record(self, description: str, category_id: str) -> None:
        self._choices[description] = category_id
        self._path.write_text(json.dumps(self._choices))


def load_keyword_rules(path: Path) -> List[KeywordRule]:
    """
    Load the owner's user-defined keyword rules from a JSON file of
    `{"keyword": ..., "category_id": ...}` entries. Returns an empty list
    when the file doesn't exist yet - this is user-authored configuration,
    not something the tool writes itself.
    """
    if not path.exists():
        return []
    return [
        KeywordRule(keyword=entry["keyword"], category_id=entry["category_id"])
        for entry in json.loads(path.read_text())
    ]


def suggest_category(
    description: str,
    history: Union[Dict[str, str], CategorySuggestionHistory],
    keyword_rules: Iterable[KeywordRule],
) -> Optional[str]:
    """
    Resolve a Category suggestion for an Expense description: the owner's
    own prior description->Category choice first, falling back to the
    first matching user-defined keyword rule, else no suggestion.
    """
    history_choice = history.get(description)
    if history_choice is not None:
        return history_choice

    lowered = description.lower()
    for rule in keyword_rules:
        if rule.keyword.lower() in lowered:
            return rule.category_id

    return None
