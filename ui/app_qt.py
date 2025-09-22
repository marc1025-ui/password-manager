from core.vault import Vault

def test_vault_full_flow(tmp_path):
    db_path = tmp_path / "vault.sqlite"
    v = Vault(db_path)



    # add
    eid = v.add_entry("https://example.com", "Example", "alice", "S3cr3t!")
    assert isinstance(eid, int)

    # search (ne demande pas la clé)
    results = v.search("example")
    assert any(r.id == eid for r in results)

    # get password (décryptage)
    assert v.get_entry(eid, reveal=True).password_ct == "S3cr3t!"

    # delete
    assert v.delete(eid) is True

    # lock
    v.lock()
    import pytest
    with pytest.raises(AssertionError):
        v.get_entry(eid, reveal=True)
