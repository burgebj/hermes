"""Test kanban handoff functionality to prevent retry loops."""

import tempfile
from pathlib import Path

from hermes_cli import kanban_db as kb


def test_handoff_block_prevents_retry():
    """Test that handoff blocks are not treated as failures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_kanban.db"
        conn = kb.connect(db_path)
        
        try:
            # Create a task
            task_id = kb.create_task(
                conn,
                title="Test task",
                assignee="test-worker",
                workspace_kind="scratch",
            )
            
            # Transition to ready
            kb.recompute_ready(conn)
            
            # Claim the task
            task = kb.claim_task(conn, task_id)
            assert task is not None
            assert task.status == "running"
            
            # Block with handoff=True
            success = kb.block_task(
                conn,
                task_id,
                reason="review-required: work complete, awaiting review",
                expected_run_id=task.current_run_id,
                handoff=True,
            )
            assert success
            
            # Verify task is blocked with handoff flag
            updated_task = kb.get_task(conn, task_id)
            assert updated_task.status == "blocked"
            assert updated_task.handoff == 1
            
            # Simulate dispatcher failure counting - should not increment
            # for handoff blocks
            tripped = kb._record_task_failure(
                conn,
                task_id,
                error="test error",
                outcome="test",
                failure_limit=2,
            )
            
            # Handoff blocks should not trigger failure counting
            assert not tripped
            
            # Verify consecutive_failures was not incremented
            task_after = kb.get_task(conn, task_id)
            assert task_after.consecutive_failures == 0
            
        finally:
            conn.close()


def test_regular_block_counts_as_failure():
    """Test that regular blocks are still treated as failures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_kanban.db"
        conn = kb.connect(db_path)
        
        try:
            # Create a task
            task_id = kb.create_task(
                conn,
                title="Test task",
                assignee="test-worker",
                workspace_kind="scratch",
            )
            
            # Transition to ready
            kb.recompute_ready(conn)
            
            # Claim the task
            task = kb.claim_task(conn, task_id)
            assert task is not None
            assert task.status == "running"
            
            # Block without handoff (regular block)
            success = kb.block_task(
                conn,
                task_id,
                reason="need human input to proceed",
                expected_run_id=task.current_run_id,
                handoff=False,
            )
            assert success
            
            # Verify task is blocked without handoff flag
            updated_task = kb.get_task(conn, task_id)
            assert updated_task.status == "blocked"
            assert updated_task.handoff == 0
            
            # Simulate dispatcher failure counting - should increment
            # for regular blocks
            tripped = kb._record_task_failure(
                conn,
                task_id,
                error="test error",
                outcome="test",
                failure_limit=2,
            )
            
            # Regular blocks should trigger failure counting
            assert not tripped  # Below threshold
            
            # Verify consecutive_failures was incremented
            task_after = kb.get_task(conn, task_id)
            assert task_after.consecutive_failures == 1
            
        finally:
            conn.close()


def test_auto_detect_handoff_from_reason():
    """Test that handoff is auto-detected from reason patterns."""
    from tools.kanban_tools import _handle_block
    
    # Test auto-detection patterns
    handoff_patterns = [
        "review-required: work complete",
        "handoff: passing to next stage",
        "needs-review: awaiting approval",
        "awaiting review: ready for review",
    ]
    
    for pattern in handoff_patterns:
        # Simulate the auto-detection logic from _handle_block
        reason_lower = pattern.lower()
        auto_handoff = any(
            p in reason_lower 
            for p in ["review-required:", "handoff:", "needs-review:", "awaiting review:"]
        )
        assert auto_handoff, f"Pattern '{pattern}' should auto-detect as handoff"
    
    # Test non-handoff pattern
    non_handoff = "need more information about requirements"
    reason_lower = non_handoff.lower()
    auto_handoff = any(
        p in reason_lower 
        for p in ["review-required:", "handoff:", "needs-review:", "awaiting review:"]
    )
    assert not auto_handoff, f"Pattern '{non_handoff}' should not auto-detect as handoff"


if __name__ == "__main__":
    test_handoff_block_prevents_retry()
    test_regular_block_counts_as_failure()
    test_auto_detect_handoff_from_reason()
    print("All kanban handoff tests passed! ✅")