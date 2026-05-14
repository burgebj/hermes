from plugins.context_engine.lcm.store import ImmutableStore


def test_append_returns_sequential_ids():
    store = ImmutableStore()
    id0 = store.append({"role": "user", "content": "hello"})
    id1 = store.append({"role": "assistant", "content": "hi"})
    id2 = store.append({"role": "user", "content": "how are you?"})
    assert id0 == 0
    assert id1 == 1
    assert id2 == 2


def test_get_valid_id():
    store = ImmutableStore()
    store.append({"role": "user", "content": "message zero"})
    store.append({"role": "assistant", "content": "message one"})
    msg = store.get(1)
    assert msg is not None
    assert msg["content"] == "message one"


def test_get_invalid_id():
    store = ImmutableStore()
    store.append({"role": "user", "content": "only message"})
    assert store.get(5) is None
    assert store.get(-1) is None


def test_get_many_mixed():
    store = ImmutableStore()
    store.append({"role": "user", "content": "msg0"})
    store.append({"role": "assistant", "content": "msg1"})
    store.append({"role": "user", "content": "msg2"})
    # IDs 0 and 2 are valid; 99 is not
    results = store.get_many([0, 99, 2])
    assert len(results) == 2
    ids = [mid for mid, _ in results]
    assert 0 in ids
    assert 2 in ids
    assert 99 not in ids


def test_len():
    store = ImmutableStore()
    assert len(store) == 0
    store.append({"role": "user", "content": "a"})
    store.append({"role": "user", "content": "b"})
    store.append({"role": "user", "content": "c"})
    assert len(store) == 3
