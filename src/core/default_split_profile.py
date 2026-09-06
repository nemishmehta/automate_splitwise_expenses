import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, Optional

from src.core.models import SplitMethod


@dataclass(frozen=True)
class SplitProfile:
    """
    A previously-used Split, stripped of any particular Expense's total: the
    method plus the raw per-Participant values the owner entered (a
    percentage for PERCENTAGE, an exact amount for EXACT), or no values at
    all for EQUAL, which needs none to be recomputed against a new total.
    """

    method: SplitMethod
    values: Optional[Dict[str, Decimal]]


class DefaultSplitProfileStore:
    """
    Durable local record of the Default Split Profile for each distinct set
    of Participants: the Split (method + values) chosen the first time that
    exact set was used together, reused as a pre-fillable suggestion on
    later Expenses involving the same set. Backed by a JSON file, keyed by
    the Participant id set (order-independent) so {A, B} and {B, A} share
    one profile while {A} and {A, B} stay independent.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._profiles: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        if self._path.exists():
            return json.loads(self._path.read_text())
        return {}

    @staticmethod
    def _key(participant_ids: Iterable[str]) -> str:
        return ",".join(sorted(set(participant_ids)))

    def get(self, participant_ids: Iterable[str]) -> Optional[SplitProfile]:
        stored = self._profiles.get(self._key(participant_ids))
        if stored is None:
            return None

        values = stored["values"]
        return SplitProfile(
            method=SplitMethod(stored["method"]),
            values=(
                None
                if values is None
                else {
                    participant_id: Decimal(value)
                    for participant_id, value in values.items()
                }
            ),
        )

    def record(
        self, participant_ids: Iterable[str], profile: SplitProfile
    ) -> None:
        self._profiles[self._key(participant_ids)] = {
            "method": profile.method.value,
            "values": (
                None
                if profile.values is None
                else {
                    participant_id: str(value)
                    for participant_id, value in profile.values.items()
                }
            ),
        }
        self._path.write_text(json.dumps(self._profiles))
