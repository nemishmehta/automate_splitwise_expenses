from decimal import ROUND_DOWN, Decimal
from typing import Sequence

from src.core.models import Share, Split, SplitMethod

_CENT = Decimal("0.01")


def compute_equal_split(
    participant_ids: Sequence[str],
    total: Decimal,
    payer_id: str,
) -> Split:
    """
    Divide `total` equally across `participant_ids` (2+), rounded down to
    the cent. Any leftover remainder from the rounding is assigned to
    `payer_id`'s Share so the Shares always sum back to `total`.
    """
    if payer_id not in participant_ids:
        raise ValueError(
            f"payer_id {payer_id!r} must be one of the split "
            "participant_ids."
        )

    base_share = (total / len(participant_ids)).quantize(
        _CENT, rounding=ROUND_DOWN
    )
    remainder = total - (base_share * len(participant_ids))

    shares = tuple(
        Share(
            participant_id=participant_id,
            owed_amount=(
                base_share + remainder
                if participant_id == payer_id
                else base_share
            ),
        )
        for participant_id in participant_ids
    )
    return Split(method=SplitMethod.EQUAL, shares=shares)
