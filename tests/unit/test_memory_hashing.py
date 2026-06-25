"""Unit tests for memory hashing."""

from synthesis.packages.memory.hashing import canonical_memory_json, memory_commit_hash


class TestMemoryHashing:
    def test_deterministic_key_order(self):
        obj1 = {"b": 2, "a": 1, "c": 3}
        obj2 = {"c": 3, "a": 1, "b": 2}
        assert canonical_memory_json(obj1) == canonical_memory_json(obj2)

    def test_memory_commit_hash_deterministic(self):
        obj1 = {"key": "value", "number": 42}
        obj2 = {"number": 42, "key": "value"}
        h1 = memory_commit_hash(obj1)
        h2 = memory_commit_hash(obj2)
        assert h1 == h2

    def test_hash_differs_for_different_data(self):
        h1 = memory_commit_hash({"a": 1})
        h2 = memory_commit_hash({"a": 2})
        assert h1 != h2
