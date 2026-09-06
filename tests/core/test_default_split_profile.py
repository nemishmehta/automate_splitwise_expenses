from decimal import Decimal

from src.core.default_split_profile import (
    DefaultSplitProfileStore,
    SplitProfile,
)
from src.core.models import SplitMethod


def test_returns_none_for_a_participant_set_with_no_recorded_profile(
    tmp_path,
):
    store = DefaultSplitProfileStore(tmp_path / "profiles.json")

    assert store.get(["p1", "p2"]) is None


def test_records_and_returns_an_equal_split_profile_with_no_values(
    tmp_path,
):
    store = DefaultSplitProfileStore(tmp_path / "profiles.json")

    store.record(
        ["p1", "p2"], SplitProfile(method=SplitMethod.EQUAL, values=None)
    )

    profile = store.get(["p1", "p2"])
    assert profile.method == SplitMethod.EQUAL
    assert profile.values is None


def test_records_and_returns_a_percentage_split_profile_with_values(
    tmp_path,
):
    store = DefaultSplitProfileStore(tmp_path / "profiles.json")

    store.record(
        ["p1", "p2"],
        SplitProfile(
            method=SplitMethod.PERCENTAGE,
            values={"p1": Decimal("50"), "p2": Decimal("50")},
        ),
    )

    profile = store.get(["p1", "p2"])
    assert profile.method == SplitMethod.PERCENTAGE
    assert profile.values == {"p1": Decimal("50"), "p2": Decimal("50")}


def test_lookup_is_order_independent(tmp_path):
    store = DefaultSplitProfileStore(tmp_path / "profiles.json")
    store.record(
        ["p1", "p2"], SplitProfile(method=SplitMethod.EQUAL, values=None)
    )

    assert store.get(["p2", "p1"]) is not None


def test_two_different_participant_sets_have_independent_profiles(
    tmp_path,
):
    store = DefaultSplitProfileStore(tmp_path / "profiles.json")
    store.record(["p1"], SplitProfile(method=SplitMethod.EQUAL, values=None))

    assert store.get(["p1", "p2"]) is None
    assert store.get(["p1"]) is not None


def test_recording_a_new_profile_overrides_the_previous_one_for_that_set(
    tmp_path,
):
    store = DefaultSplitProfileStore(tmp_path / "profiles.json")
    store.record(
        ["p1", "p2"],
        SplitProfile(
            method=SplitMethod.PERCENTAGE,
            values={"p1": Decimal("50"), "p2": Decimal("50")},
        ),
    )

    store.record(
        ["p1", "p2"],
        SplitProfile(
            method=SplitMethod.EXACT,
            values={"p1": Decimal("5"), "p2": Decimal("15")},
        ),
    )

    profile = store.get(["p1", "p2"])
    assert profile.method == SplitMethod.EXACT
    assert profile.values == {"p1": Decimal("5"), "p2": Decimal("15")}


def test_profile_persists_across_instances(tmp_path):
    path = tmp_path / "profiles.json"
    DefaultSplitProfileStore(path).record(
        ["p1", "p2"],
        SplitProfile(
            method=SplitMethod.EXACT,
            values={"p1": Decimal("5"), "p2": Decimal("15")},
        ),
    )

    reloaded = DefaultSplitProfileStore(path)

    profile = reloaded.get(["p1", "p2"])
    assert profile.method == SplitMethod.EXACT
    assert profile.values == {"p1": Decimal("5"), "p2": Decimal("15")}
