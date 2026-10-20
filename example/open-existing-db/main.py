"""Example: Opening an Existing ObjectBox Database

This example demonstrates that ObjectBox transparently opens an existing
database when the given directory already contains one (data.mdb), and
creates a new one if it doesn't. This means any program that uses the
same entity model can read a database written by another program or even
another ObjectBox SDK (e.g. Android/Java, Swift, Dart), as long as the
model is compatible.

Usage:
    # Step 1 – write some data (creates the database on disk)
    python main.py write

    # Step 2 – open the same database and read the data back
    python main.py read

    # Reset: remove the database directory and start fresh
    python main.py reset
"""

import os
import sys
import shutil

from objectbox import Entity, Id, Int32, String, Store

DB_DIRECTORY = "notes-db"


@Entity()
class Note:
    id = Id()
    title = String()
    body = String()
    priority = Int32()


def open_store() -> Store:
    """Open (or create) the ObjectBox store in DB_DIRECTORY.

    ObjectBox will:
    - Create the directory and a brand-new database if it does not exist yet.
    - Open the existing database transparently if it already exists.
    """
    return Store(directory=DB_DIRECTORY)


def write_data():
    """Insert sample notes into the database."""
    store = open_store()
    box = store.box(Note)

    notes = [
        Note(title="Buy groceries", body="Milk, eggs, bread", priority=1),
        Note(title="Read ObjectBox docs", body="https://docs.objectbox.io", priority=2),
        Note(title="Open-source contribution", body="Submit a pull request today!", priority=3),
    ]

    for note in notes:
        box.put(note)

    print(f"Wrote {len(notes)} notes to '{DB_DIRECTORY}'.")
    print("Run 'python main.py read' to open the same database and list them.")
    store.close()


def read_data():
    """Open the existing database and print all stored notes."""
    if not os.path.isdir(DB_DIRECTORY):
        print(f"Database directory '{DB_DIRECTORY}' not found.")
        print("Run 'python main.py write' first to create and populate it.")
        sys.exit(1)

    store = open_store()
    box = store.box(Note)
    notes = box.get_all()

    if not notes:
        print("No notes found in the database.")
    else:
        print(f"Found {len(notes)} note(s) in '{DB_DIRECTORY}':\n")
        print(f"{'ID':>3}  {'Priority':>8}  {'Title':<30}  Body")
        print("-" * 70)
        for note in notes:
            print(f"{note.id:>3}  {note.priority:>8}  {note.title:<30}  {note.body}")

    store.close()


def reset_data():
    """Delete the database directory so the example can be run from scratch."""
    if os.path.isdir(DB_DIRECTORY):
        shutil.rmtree(DB_DIRECTORY)
        print(f"Removed '{DB_DIRECTORY}'. Run 'python main.py write' to start fresh.")
    else:
        print(f"Nothing to reset – '{DB_DIRECTORY}' does not exist.")


if __name__ == "__main__":
    commands = {"write": write_data, "read": read_data, "reset": reset_data}

    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print("Usage: python main.py <write|read|reset>")
        sys.exit(1)

    commands[sys.argv[1]]()
