from __future__ import annotations
from dataclasses import dataclass, field

MessageId = int


@dataclass
class SummaryNode:
    id: int
    source_ids: list[MessageId]
    child_summaries: list[int] = field(default_factory=list)
    text: str = ""
    tokens: int = 0
    level: int = 1


@dataclass
class SummaryDag:
    nodes: list[SummaryNode] = field(default_factory=list)
    _next_id: int = 0

    def create_node(
        self,
        source_ids: list[MessageId],
        text: str,
        level: int,
        tokens: int = 0,
        children: list[int] | None = None,
    ) -> SummaryNode:
        node = SummaryNode(
            id=self._next_id,
            source_ids=source_ids,
            child_summaries=children or [],
            text=text,
            tokens=tokens,
            level=level,
        )
        self.nodes.append(node)
        self._next_id += 1
        return node

    def get(self, node_id: int) -> SummaryNode | None:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def all_source_ids(self, node_id: int) -> list[MessageId]:
        node = self.get(node_id)
        if node is None:
            return []
        result = list(node.source_ids)
        for child_id in node.child_summaries:
            result.extend(self.all_source_ids(child_id))
        return result

    def __len__(self) -> int:
        return len(self.nodes)

    @property
    def is_empty(self) -> bool:
        return len(self.nodes) == 0
