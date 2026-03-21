#!/usr/bin/env python3
"""Integration verification for approval flow components."""

import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size
        print(f"✓ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"✗ {description}: {filepath} (NOT FOUND)")
        return False


def check_backend_integration() -> bool:
    """Verify backend integration."""
    print("=== Backend Integration ===\n")

    all_ok = True

    # Check approval routes
    all_ok &= check_file_exists("foundrai/api/routes/approvals.py", "Approval routes")

    # Check config with timeout
    all_ok &= check_file_exists("foundrai/config.py", "Configuration")

    # Check engine with timeout support
    all_ok &= check_file_exists("foundrai/orchestration/engine.py", "Sprint engine")

    return all_ok


def check_frontend_integration() -> bool:
    """Verify frontend integration."""
    print("\n=== Frontend Integration ===\n")

    all_ok = True

    # Core approval components
    all_ok &= check_file_exists(
        "frontend/src/components/approvals/ApprovalBanner.tsx", "Approval banner"
    )
    all_ok &= check_file_exists(
        "frontend/src/components/approvals/ApprovalQueue.tsx", "Approval queue"
    )
    all_ok &= check_file_exists(
        "frontend/src/components/approvals/ApprovalCard.tsx", "Approval card (enhanced)"
    )

    # New components
    all_ok &= check_file_exists(
        "frontend/src/components/approvals/ApprovalTimer.tsx", "Countdown timer"
    )
    all_ok &= check_file_exists(
        "frontend/src/components/approvals/ContextRenderer.tsx", "Context renderer"
    )

    # Store and utilities
    all_ok &= check_file_exists(
        "frontend/src/stores/approvalStore.ts", "Approval store (with notifications)"
    )
    all_ok &= check_file_exists("frontend/src/utils/notifications.ts", "Notification utility")
    all_ok &= check_file_exists("frontend/src/utils/sound.ts", "Sound utility")

    # Assets
    all_ok &= check_file_exists("frontend/src/assets/notification.mp3", "Notification sound")

    # API client
    all_ok &= check_file_exists("frontend/src/api/approvals.ts", "Approval API client")

    return all_ok


def check_documentation() -> bool:
    """Verify documentation exists."""
    print("\n=== Documentation ===\n")

    all_ok = True

    all_ok &= check_file_exists("E2E_VERIFICATION_GUIDE.md", "E2E testing guide")
    all_ok &= check_file_exists("VERIFICATION_SUMMARY.md", "Verification summary")
    all_ok &= check_file_exists("verify_backend.py", "Backend verification script")

    return all_ok


def check_typescript_imports() -> bool:
    """Check TypeScript imports are correct."""
    print("\n=== TypeScript Import Verification ===\n")

    # Check ApprovalCard imports ContextRenderer
    approval_card = Path("frontend/src/components/approvals/ApprovalCard.tsx")
    if approval_card.exists():
        content = approval_card.read_text()
        if "import { ContextRenderer }" in content:
            print("✓ ApprovalCard imports ContextRenderer")
        else:
            print("✗ ApprovalCard missing ContextRenderer import")
            return False

        if "import { Clock }" in content:
            print("✓ ApprovalCard imports Clock icon")
        else:
            print("✗ ApprovalCard missing Clock icon import")
            return False
    else:
        return False

    # Check approvalStore imports notification utilities
    store = Path("frontend/src/stores/approvalStore.ts")
    if store.exists():
        content = store.read_text()
        if "import { showApprovalNotification }" in content:
            print("✓ approvalStore imports showApprovalNotification")
        else:
            print("✗ approvalStore missing showApprovalNotification import")
            return False

        if "import { playNotificationSound }" in content:
            print("✓ approvalStore imports playNotificationSound")
        else:
            print("✗ approvalStore missing playNotificationSound import")
            return False
    else:
        return False

    # Check ApprovalQueue uses ApprovalCard
    queue = Path("frontend/src/components/approvals/ApprovalQueue.tsx")
    if queue.exists():
        content = queue.read_text()
        if "import { ApprovalCard }" in content and "<ApprovalCard" in content:
            print("✓ ApprovalQueue uses ApprovalCard")
        else:
            print("✗ ApprovalQueue not using ApprovalCard correctly")
            return False
    else:
        return False

    return True


def main():
    """Run all integration checks."""
    print("╔═══════════════════════════════════════════════╗")
    print("║   Approval Flow Integration Verification     ║")
    print("╚═══════════════════════════════════════════════╝\n")

    backend_ok = check_backend_integration()
    frontend_ok = check_frontend_integration()
    docs_ok = check_documentation()
    imports_ok = check_typescript_imports()

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    results = {
        "Backend Integration": backend_ok,
        "Frontend Integration": frontend_ok,
        "Documentation": docs_ok,
        "TypeScript Imports": imports_ok,
    }

    for name, ok in results.items():
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{name:.<40} {status}")

    all_ok = all(results.values())

    if all_ok:
        print("\n✅ All integration checks passed!")
        print("\nNext steps:")
        print("1. Review E2E_VERIFICATION_GUIDE.md")
        print("2. Start backend: foundrai serve")
        print("3. Start frontend: cd frontend && npm run dev")
        print("4. Follow manual testing steps in guide")
        return 0
    else:
        print("\n❌ Some integration checks failed!")
        print("Review errors above and fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
