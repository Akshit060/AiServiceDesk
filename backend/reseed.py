"""
Developer-only reseed script.
Deletes the existing database and restarts with a fresh seed.

Usage:
    python reseed.py

This is NEVER run automatically during normal startup.
"""
import os
import sys


def main():
    db_path = "servicedesk.db"

    if os.path.exists(db_path):
        confirm = input(f"This will DELETE {db_path} and reseed from scratch. Continue? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            sys.exit(0)
        os.remove(db_path)
        print(f"Deleted {db_path}.")
    else:
        print("No existing database found. A fresh seed will occur on next startup.")

    print("Start the application to trigger a fresh seed:")
    print("  uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
