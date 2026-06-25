"""Unit tests for immutable policy."""

import pytest
from synthesis.packages.policy.immutable import is_immutable, assert_mutable, validate_mutation


class TestImmutablePolicy:
    def test_immutable_key_blocked(self):
        assert is_immutable("local_first")
        assert is_immutable("routing_weights")
        assert is_immutable("safety_policy")

    def test_mutable_key_allowed(self):
        assert not is_immutable("custom_config")
        assert not is_immutable("user_preference")

    def test_assert_mutable_raises(self):
        with pytest.raises(ValueError, match="Runtime mutation"):
            assert_mutable("local_first")

    def test_assert_mutable_passes(self):
        assert_mutable("custom_config")  # Should not raise

    def test_validate_mutation(self):
        allowed, blocked = validate_mutation({
            "local_first": True,
            "custom_config": "value",
        })
        assert not allowed
        assert "local_first" in blocked

    def test_validate_mutation_all_allowed(self):
        allowed, blocked = validate_mutation({
            "custom_config": "value",
            "user_preference": "dark",
        })
        assert allowed
        assert len(blocked) == 0
