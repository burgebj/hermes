from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

MessageId = int

_PRUNED_SENTINEL = None  # slots in _messages are set to None when pruned


@dataclass
class ImmutableStore:
    _messages: list[dict[str, Any] | None] = field(default_factory=list)
    _pruned: set[MessageId] = field(default_factory=set)

    def append(self, message: dict[str, Any]) -> MessageId:
        msg_id = len(self._messages)
        self._messages.append(message)
        return msg_id

    def get(self, msg_id: MessageId) -> dict[str, Any] | None:
        if 0 <= msg_id < len(self._messages) and msg_id not in self._pruned:
            return self._messages[msg_id]
        return None

    def get_many(
        self, msg_ids: list[MessageId]
    ) -> list[tuple[MessageId, dict[str, Any]]]:
        return [
            (mid, self._messages[mid])
            for mid in msg_ids
            if 0 <= mid < len(self._messages) and mid not in self._pruned
        ]

    def prune(self, keep_ids: set[MessageId], max_size: int) -> int:
        """Mark old unreferenced messages as pruned until active_count <= max_size.

        Pruning is performed in ascending order (oldest first).  Messages in
        keep_ids are never pruned regardless of age.

        Args:
            keep_ids: MessageIds that must not be pruned (referenced + pinned).
            max_size: Target maximum for active_count after pruning.

        Returns:
            Number of newly pruned messages.
        """
        to_prune = max(0, self.active_count - max_size)
        if to_prune == 0:
            return 0

        newly_pruned = 0
        for msg_id in range(len(self._messages)):
            if newly_pruned >= to_prune:
                break
            if msg_id in self._pruned:
                continue  # already pruned
            if msg_id in keep_ids:
                continue  # protected
            # Prune it
            self._messages[msg_id] = _PRUNED_SENTINEL
            self._pruned.add(msg_id)
            newly_pruned += 1

        return newly_pruned

    @property
    def pruned_ids(self) -> set[MessageId]:
        """Return the set of currently pruned MessageIds."""
        return set(self._pruned)

    @property
    def active_count(self) -> int:
        """Number of non-pruned messages in the store."""
        return len(self._messages) - len(self._pruned)

    def __len__(self) -> int:
        return len(self._messages)
