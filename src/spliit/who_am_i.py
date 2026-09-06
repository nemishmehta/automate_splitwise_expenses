import json
from pathlib import Path
from typing import Dict, List, Optional


class WhoAmI:
    """
    Durable local record of the Payer Configuration: which Participant is
    "you" for each Spliit Group, since Spliit has no login/account concept
    to derive this from. Backed by a JSON file, keyed group_id ->
    participant_id. Set once per Group via a one-time setup step, then
    reused on every later Expense for that Group without re-asking.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._payer_ids: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return {}

    def get(self, group_id: str) -> Optional[str]:
        return self._payer_ids.get(group_id)

    def known_group_ids(self) -> List[str]:
        return list(self._payer_ids.keys())

    def set(self, group_id: str, participant_id: str) -> None:
        self._payer_ids[group_id] = participant_id
        self._path.write_text(json.dumps(self._payer_ids))
