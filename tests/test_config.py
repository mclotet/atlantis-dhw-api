import pytest
from pydantic import ValidationError

from app.config import Settings


def test_config_from_toml(tmp_path, monkeypatch):
    (tmp_path / "atlantis.toml").write_text(
        'atl_service_name = "dhw-api"\n'
        'atl_group_id = "basement"\n'
        'atl_env = "pro"\n'
        'dhw_influxdb_url = "http://influxdb:8086"\n'
        'dhw_influxdb_org = "atlantis"\n'
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DHW_INFLUXDB_TOKEN", "test-token")
    # Clear any cached module-level settings by instantiating fresh
    s = Settings()
    assert s.atl_service_name == "dhw-api"
    assert s.atl_group_id == "basement"
    assert s.atl_env == "pro"
    assert s.dhw_influxdb_token == "test-token"


def test_env_overrides_toml(tmp_path, monkeypatch):
    (tmp_path / "atlantis.toml").write_text(
        'atl_service_name = "dhw-api"\n'
        'atl_group_id = "basement"\n'
        'atl_env = "pro"\n'
        'dhw_influxdb_url = "http://influxdb:8086"\n'
        'dhw_influxdb_org = "atlantis"\n'
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DHW_INFLUXDB_TOKEN", "test-token")
    monkeypatch.setenv("ATL_ENV", "itg")

    s = Settings()
    assert s.atl_env == "itg"


def test_missing_token_raises(tmp_path, monkeypatch):
    (tmp_path / "atlantis.toml").write_text(
        'atl_service_name = "dhw-api"\n'
        'dhw_influxdb_url = "http://influxdb:8086"\n'
        'dhw_influxdb_org = "atlantis"\n'
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DHW_INFLUXDB_TOKEN", raising=False)

    with pytest.raises(ValidationError):
        Settings()
