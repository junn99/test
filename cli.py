#!/usr/bin/env python
"""Command-line interface for Notion Knowledge Agent."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.notion_agent import create_agent
from src.sync.daily_sync import run_daily_sync, run_full_sync
from src.scheduler.jobs import get_scheduler
from src.memory.user_profile import UserProfile
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def cmd_sync(args):
    """Run synchronization."""
    if args.full:
        logger.info("Starting full sync...")
        result = run_full_sync()
    else:
        logger.info(f"Starting incremental sync (last {args.days} days)...")
        result = run_daily_sync(days=args.days)

    if "error" in result:
        print(f"❌ Sync failed: {result['error']}")
        return 1

    print(f"✅ Sync completed!")
    print(f"   Pages updated: {result.get('pages_updated', 0)}")
    print(f"   Pages failed: {result.get('pages_failed', 0)}")
    print(f"   Duration: {result.get('duration_seconds', 0):.2f}s")
    return 0


def cmd_chat(args):
    """Interactive chat mode."""
    print("Notion Knowledge Agent - Chat Mode")
    print("Type 'exit' or 'quit' to end the conversation\n")

    agent = create_agent()

    while True:
        try:
            query = input("You: ").strip()

            if query.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if not query:
                continue

            print("\nAgent: ", end="", flush=True)
            response = agent.chat(query)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")

    return 0


def cmd_analyze(args):
    """Analyze workspace."""
    print("Analyzing Notion workspace...\n")

    agent = create_agent()
    analysis = agent.analyze_workspace()

    print(analysis)
    return 0


def cmd_report(args):
    """Generate report."""
    print(f"Generating {args.type} report...\n")

    agent = create_agent()
    report = agent.generate_report(args.type)

    print(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n✅ Report saved to: {args.output}")

    return 0


def cmd_profile(args):
    """Manage user profile."""
    profile = UserProfile()

    if args.show:
        print(profile.get_profile_summary())

    if args.set:
        key, value = args.set.split("=", 1)
        profile.set_preference(key, value)
        print(f"✅ Set {key} = {value}")

    return 0


def cmd_scheduler(args):
    """Manage scheduler."""
    scheduler = get_scheduler()

    if args.start:
        if not scheduler.is_running:
            scheduler.start()
            print("✅ Scheduler started")
        else:
            print("⚠️  Scheduler is already running")

    elif args.stop:
        if scheduler.is_running:
            scheduler.stop()
            print("✅ Scheduler stopped")
        else:
            print("⚠️  Scheduler is not running")

    elif args.status:
        if scheduler.is_running:
            print("✅ Scheduler is running")
            jobs = scheduler.list_jobs()
            if jobs:
                print("\nScheduled jobs:")
                for job in jobs:
                    print(f"  - {job['name']}: next run at {job['next_run']}")
        else:
            print("❌ Scheduler is not running")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Notion Knowledge Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize Notion content")
    sync_parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days to sync (default: 1)"
    )
    sync_parser.add_argument(
        "--full",
        action="store_true",
        help="Perform full sync of all pages"
    )

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze workspace")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument(
        "type",
        choices=["daily", "weekly", "monthly"],
        help="Report type"
    )
    report_parser.add_argument(
        "-o", "--output",
        help="Output file path"
    )

    # Profile command
    profile_parser = subparsers.add_parser("profile", help="Manage user profile")
    profile_parser.add_argument("--show", action="store_true", help="Show profile")
    profile_parser.add_argument("--set", help="Set preference (key=value)")

    # Scheduler command
    scheduler_parser = subparsers.add_parser("scheduler", help="Manage scheduler")
    scheduler_group = scheduler_parser.add_mutually_exclusive_group()
    scheduler_group.add_argument("--start", action="store_true", help="Start scheduler")
    scheduler_group.add_argument("--stop", action="store_true", help="Stop scheduler")
    scheduler_group.add_argument("--status", action="store_true", help="Show status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handlers
    commands = {
        "sync": cmd_sync,
        "chat": cmd_chat,
        "analyze": cmd_analyze,
        "report": cmd_report,
        "profile": cmd_profile,
        "scheduler": cmd_scheduler,
    }

    try:
        return commands[args.command](args)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
