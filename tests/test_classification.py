from core.indexer import classify, producer_overrides


def test_stock_and_general_classification_excludes_challenge_cine_and_boss():
    assert classify("GLAArmsDealer", "GLAArmsDealerCommandSet") == ("GLA", "Vanilla")
    assert classify("Chem_GLAArmsDealer", "Chem_GLAArmsDealerCommandSet") == ("GLA", "Toxin")
    assert classify("GC_Chem_GLAArmsDealer", "GC_Chem_GLAArmsDealerCommandSet") == ("", "")
    assert classify("Boss_TunnelNetwork", "Boss_GLATunnelNetworkCommandSet") == ("", "")
    assert classify("CINE_GLAInfantryWorker", "GLAWorkerCommandSet") == ("", "")


def test_vanilla_gla_uses_only_reference_producer_panels():
    assert {
        "GLAWorkerCommandSet",
        "GLACommandCenterCommandSet",
        "GLABarracksCommandSet",
        "GLAArmsDealerCommandSet",
    } <= producer_overrides()["GLA/Vanilla"]
