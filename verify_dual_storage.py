#!/usr/bin/env python3
"""Direct verification that learnings are stored in both ChromaDB and SQLite."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from foundrai.config import MemoryConfig
from foundrai.models.learning import Learning
from foundrai.persistence.database import Database
from foundrai.persistence.vector_memory import VectorMemory


async def main():
    """Verify dual storage of learnings."""
    print("=" * 70)
    print("DUAL STORAGE VERIFICATION")
    print("=" * 70)

    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        print(f"\nTest directory: {tmpdir}")

        # Step 1: Create database and VectorMemory
        print("\n[1] Setting up database and VectorMemory...")
        db = Database(str(tmppath / "test.db"))
        await db.connect()
        print("    ✓ Database connected and schema initialized")

        memory_config = MemoryConfig(chromadb_path=str(tmppath / "chroma"))
        vector_memory = VectorMemory(config=memory_config, db=db)
        print("    ✓ VectorMemory created with database connection")

        # Step 2: Create test learnings
        print("\n[2] Creating test learnings...")
        learnings = [
            Learning(
                content="Need more thorough testing before QA review",
                category="quality",
                sprint_id="sprint-001",
                project_id="test-project",
            ),
            Learning(
                content="Should add unit tests before implementation",
                category="process",
                sprint_id="sprint-001",
                project_id="test-project",
            ),
            Learning(
                content="Sprint completion rate: 75%",
                category="metrics",
                sprint_id="sprint-001",
                project_id="test-project",
            ),
        ]
        print(f"    ✓ Created {len(learnings)} test learnings")

        # Step 3: Store learnings using VectorMemory
        print("\n[3] Storing learnings via VectorMemory.store_learning()...")
        for i, learning in enumerate(learnings, 1):
            await vector_memory.store_learning(learning)
            print(f"    ✓ Stored learning {i}: [{learning.category}] {learning.content[:50]}...")

        # Step 4: Query SQLite database
        print("\n[4] Querying SQLite learnings table...")
        cursor = await db.conn.execute(
            "SELECT learning_id, project_id, sprint_id, content, category FROM learnings WHERE sprint_id = ?",
            ("sprint-001",),
        )
        sqlite_rows = await cursor.fetchall()

        sqlite_learnings = [
            {
                "id": row[0],
                "project_id": row[1],
                "sprint_id": row[2],
                "content": row[3],
                "category": row[4],
            }
            for row in sqlite_rows
        ]

        print(f"    ✓ Found {len(sqlite_learnings)} learnings in SQLite")
        for lr in sqlite_learnings:
            print(f"      - [{lr['category']}] {lr['content']}")

        # Step 5: Query ChromaDB via VectorMemory
        print("\n[5] Querying ChromaDB via VectorMemory.get_all_learnings()...")
        vector_learnings_list = await vector_memory.get_all_learnings(project_id="test-project")

        # Filter to only this sprint
        vector_learnings = [lr for lr in vector_learnings_list if lr.sprint_id == "sprint-001"]

        print(f"    ✓ Found {len(vector_learnings)} learnings in ChromaDB")
        for lr in vector_learnings:
            print(f"      - [{lr.category}] {lr.content}")

        # Step 6: Verify counts match
        print("\n[6] Verifying dual storage consistency...")

        if len(sqlite_learnings) == 0:
            print("    ✗ FAILED: No learnings found in SQLite!")
            return False

        if len(vector_learnings) == 0:
            print("    ✗ FAILED: No learnings found in ChromaDB!")
            return False

        if len(sqlite_learnings) != len(vector_learnings):
            print(
                f"    ✗ FAILED: Count mismatch! SQLite: {len(sqlite_learnings)}, ChromaDB: {len(vector_learnings)}"
            )
            return False

        print(f"    ✓ Count matches: {len(sqlite_learnings)} learnings in both stores")

        # Step 7: Verify content matches
        print("\n[7] Verifying content matches...")

        sqlite_contents = {lr["content"] for lr in sqlite_learnings}
        vector_contents = {lr.content for lr in vector_learnings}

        if sqlite_contents != vector_contents:
            print("    ✗ FAILED: Content mismatch!")
            print(f"      SQLite only: {sqlite_contents - vector_contents}")
            print(f"      ChromaDB only: {vector_contents - sqlite_contents}")
            return False

        print("    ✓ All content matches between stores")

        # Step 8: Verify IDs match
        print("\n[8] Verifying IDs and metadata match...")

        vector_by_id = {lr.id: lr for lr in vector_learnings}

        for sqlite_lr in sqlite_learnings:
            learning_id = sqlite_lr["id"]

            if learning_id not in vector_by_id:
                print(f"    ✗ FAILED: Learning {learning_id} not found in ChromaDB!")
                return False

            vector_lr = vector_by_id[learning_id]

            # Verify all metadata
            if vector_lr.project_id != sqlite_lr["project_id"]:
                print(f"    ✗ FAILED: Project ID mismatch for {learning_id}")
                return False

            if vector_lr.sprint_id != sqlite_lr["sprint_id"]:
                print(f"    ✗ FAILED: Sprint ID mismatch for {learning_id}")
                return False

            if vector_lr.content != sqlite_lr["content"]:
                print(f"    ✗ FAILED: Content mismatch for {learning_id}")
                return False

            if vector_lr.category != sqlite_lr["category"]:
                print(f"    ✗ FAILED: Category mismatch for {learning_id}")
                return False

        print("    ✓ All IDs and metadata match perfectly")

        # Step 9: Test persistence (simulate restart)
        print("\n[9] Testing persistence across VectorMemory recreation...")

        # Create new VectorMemory instance (simulating app restart)
        vector_memory2 = VectorMemory(config=memory_config, db=db)

        # Query again
        vector_learnings2 = await vector_memory2.get_all_learnings(project_id="test-project")
        vector_learnings2 = [lr for lr in vector_learnings2 if lr.sprint_id == "sprint-001"]

        if len(vector_learnings2) != len(learnings):
            print(
                f"    ✗ FAILED: Persistence check failed! Expected {len(learnings)}, found {len(vector_learnings2)}"
            )
            return False

        print(f"    ✓ Persistence verified: {len(vector_learnings2)} learnings survived restart")

        # Cleanup
        await db.close()

        # Final summary
        print("\n" + "=" * 70)
        print("✅ VERIFICATION PASSED!")
        print("=" * 70)
        print("\nSummary:")
        print(f"  • Stored {len(learnings)} learnings via VectorMemory")
        print(f"  • SQLite contains {len(sqlite_learnings)} learnings")
        print(f"  • ChromaDB contains {len(vector_learnings)} learnings")
        print("  • All content, IDs, and metadata match perfectly")
        print("  • Learnings persist across VectorMemory recreation")
        print("\n✅ Dual storage is working correctly!")

        return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
