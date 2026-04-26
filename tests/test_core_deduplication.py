from core.deduplication import build_dedup_key


def test_build_dedup_key_normalizes_name_and_phone_whitespace():
    key_a = build_dedup_key("  ALICE  ", "  +123 ", 1, 2)
    key_b = build_dedup_key("alice", "+123", 1, 2)
    assert key_a == key_b


def test_build_dedup_key_changes_with_business_fields():
    baseline = build_dedup_key("alice", "+123", 1, 2)
    changed_offer = build_dedup_key("alice", "+123", 2, 2)
    changed_affiliate = build_dedup_key("alice", "+123", 1, 3)
    assert baseline != changed_offer
    assert baseline != changed_affiliate
