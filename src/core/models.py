from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, Tuple


class SplitMethod(Enum):
    EQUAL = "equal"
    EXACT = "exact"
    PERCENTAGE = "percentage"


@dataclass(frozen=True)
class Participant:
    """Anyone selectable to share the cost of an Expense, including you."""

    id: str
    name: str


@dataclass(frozen=True)
class Group:
    """A named, persistent collection of Participants."""

    id: str
    name: str
    participants: Tuple[Participant, ...]


@dataclass(frozen=True)
class Category:
    id: str
    name: str


@dataclass(frozen=True)
class Share:
    """A single Participant's owed amount within a Split."""

    participant_id: str
    owed_amount: Decimal


@dataclass(frozen=True)
class Split:
    """
    The method used to divide a Shared Expense's cost, plus each
    Participant's resulting Share. Always covers 2 or more Participants.
    """

    method: SplitMethod
    shares: Tuple[Share, ...]

    def __post_init__(self) -> None:
        if len(self.shares) < 2:
            raise ValueError(
                "A Split must cover 2 or more Participants, got "
                f"{len(self.shares)}."
            )

        participant_ids = [share.participant_id for share in self.shares]
        if len(set(participant_ids)) != len(participant_ids):
            raise ValueError(
                "A Split cannot list the same Participant more than once."
            )


@dataclass(frozen=True)
class Expense:
    """
    A cost recorded under a Group. A Personal Expense (a Group containing
    only the Payer) has no Split; a Shared Expense always has one.
    """

    group_id: str
    description: str
    amount: Decimal
    currency: str
    date: date
    payer_id: str
    category_id: Optional[str]
    split: Optional[Split]
