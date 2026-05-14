from plugins.context_engine.lcm.dag import SummaryDag, SummaryNode, MessageId


def test_create_node():
    dag = SummaryDag()
    node = dag.create_node(source_ids=[0, 1, 2], text="summary text", level=1, tokens=42)
    assert node.id == 0
    assert node.source_ids == [0, 1, 2]
    assert node.text == "summary text"
    assert node.tokens == 42
    assert node.level == 1


def test_create_multiple_nodes():
    dag = SummaryDag()
    n0 = dag.create_node(source_ids=[0], text="first", level=1)
    n1 = dag.create_node(source_ids=[1], text="second", level=1)
    n2 = dag.create_node(source_ids=[2], text="third", level=1)
    assert n0.id == 0
    assert n1.id == 1
    assert n2.id == 2


def test_get_existing():
    dag = SummaryDag()
    dag.create_node(source_ids=[5, 6], text="hello", level=2, tokens=10)
    node = dag.get(0)
    assert node is not None
    assert node.id == 0
    assert node.source_ids == [5, 6]
    assert node.text == "hello"
    assert node.level == 2
    assert node.tokens == 10


def test_get_nonexistent():
    dag = SummaryDag()
    dag.create_node(source_ids=[0], text="only node", level=1)
    assert dag.get(99) is None
    assert dag.get(-1) is None


def test_all_source_ids_flat():
    dag = SummaryDag()
    dag.create_node(source_ids=[10, 11, 12], text="leaf", level=1)
    result = dag.all_source_ids(0)
    assert result == [10, 11, 12]


def test_all_source_ids_recursive():
    dag = SummaryDag()
    # child summaries: node 0 and node 1
    child0 = dag.create_node(source_ids=[0, 1], text="child0", level=1)
    child1 = dag.create_node(source_ids=[2, 3], text="child1", level=1)
    # parent references both children as child_summaries, no direct source_ids
    parent = dag.create_node(
        source_ids=[],
        text="parent",
        level=2,
        children=[child0.id, child1.id],
    )
    result = dag.all_source_ids(parent.id)
    assert sorted(result) == [0, 1, 2, 3]


def test_empty_dag():
    dag = SummaryDag()
    assert len(dag) == 0
    assert dag.is_empty is True
