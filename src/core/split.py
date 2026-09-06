from decimal import ROUND_DOWN, Decimal
from typing import Mapping, Sequence

from src.core.models import Share, Split, SplitMethod

_CENT = Decimal("0.01")
_TOLERANCE = Decimal("0.01")


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


def compute_exact_split(
    amounts: Mapping[str, Decimal],
    total: Decimal,
    payer_id: str,
) -> Split:
    """
    Build a Split from explicit per-Participant amounts. Raises ValueError
    if the amounts don't sum to `total` within a small rounding tolerance,
    or if `payer_id` isn't among the given Participants.
    """
    if payer_id not in amounts:
        raise ValueError(
            f"payer_id {payer_id!r} must be one of the split "
            "participant_ids."
        )
    if abs(sum(amounts.values()) - total) > _TOLERANCE:
        raise ValueError(
            f"Exact Amount shares {dict(amounts)} must sum to {total}, "
            f"got {sum(amounts.values())}."
        )

    shares = tuple(
        Share(participant_id=participant_id, owed_amount=amount)
        for participant_id, amount in amounts.items()
    )
    return Split(method=SplitMethod.EXACT, shares=shares)


def compute_percentage_split(
    percentages: Mapping[str, Decimal],
    total: Decimal,
    payer_id: str,
) -> Split:
    """
    Build a Split from explicit per-Participant percentages of `total`.
    Each percentage is converted to a cent-rounded amount (ROUND_DOWN),
    with any rounding remainder assigned to `payer_id`'s Share so the
    Shares always sum exactly back to `total`. Raises ValueError if the
    percentages don't sum to 100 within a small tolerance, or if
    `payer_id` isn't among the given Participants.
    """
    if payer_id not in percentages:
        raise ValueError(
            f"payer_id {payer_id!r} must be one of the split "
            "participant_ids."
        )
    if abs(sum(percentages.values()) - Decimal("100")) > _TOLERANCE:
        raise ValueError(
            f"Percentage shares {dict(percentages)} must sum to 100, got "
            f"{sum(percentages.values())}."
        )

    computed = {
        participant_id: (total * percentage / Decimal("100")).quantize(
            _CENT, rounding=ROUND_DOWN
        )
        for participant_id, percentage in percentages.items()
    }
    remainder = total - sum(computed.values())
    computed[payer_id] += remainder

    shares = tuple(
        Share(participant_id=participant_id, owed_amount=amount)
        for participant_id, amount in computed.items()
    )
    return Split(method=SplitMethod.PERCENTAGE, shares=shares)
