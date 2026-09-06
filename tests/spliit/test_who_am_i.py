from src.spliit.who_am_i import WhoAmI


def test_who_am_i_returns_none_for_an_unconfigured_group(tmp_path):
    who_am_i = WhoAmI(tmp_path / "who_am_i.json")

    assert who_am_i.get("g1") is None


def test_who_am_i_returns_the_configured_payer_for_a_group(tmp_path):
    who_am_i = WhoAmI(tmp_path / "who_am_i.json")

    who_am_i.set("g1", "p1")

    assert who_am_i.get("g1") == "p1"


def test_who_am_i_persists_the_payer_configuration_across_instances(
    tmp_path,
):
    path = tmp_path / "who_am_i.json"
    WhoAmI(path).set("g1", "p1")

    reloaded = WhoAmI(path)

    assert reloaded.get("g1") == "p1"


def test_setting_a_new_payer_overrides_the_previous_one(tmp_path):
    who_am_i = WhoAmI(tmp_path / "who_am_i.json")
    who_am_i.set("g1", "p1")

    who_am_i.set("g1", "p2")

    assert who_am_i.get("g1") == "p2"


def test_who_am_i_keeps_independent_configurations_per_group(tmp_path):
    who_am_i = WhoAmI(tmp_path / "who_am_i.json")

    who_am_i.set("g1", "p1")
    who_am_i.set("g2", "p2")

    assert who_am_i.get("g1") == "p1"
    assert who_am_i.get("g2") == "p2"
