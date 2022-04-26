# !/usr/bin/env python3
# -*- cosing: utf-8 -*-

import argparse
import sqlite3
import typing as t
from pathlib import Path


def display_workers(staff: t.List[t.Dict[str, t.Any]]) -> None:
    if staff:
        line = '+-{}-+-{}-+-{}-+-{}-+-{}-+'.format(
            '-' * 4,
            '-' * 30,
            '-' * 20,
            '-' * 15,
            '-' * 20
        )
        print(line)
        print(
            '| {:^4} | {:^30} | {:^20} | {:^15} | {:^20} |'.format(
                "№",
                "Фамилия",
                "Имя",
                "Знак зодиака",
                "Год рождения"
            )
        )
        print(line)

        for idx, worker in enumerate(staff, 1):
            print(
                '| {:^4} | {:^30} | {:^20} | {:^15} | {:^20} |'.format(
                    idx,
                    worker.get('surname', ''),
                    worker.get('name', ''),
                    worker.get('zodiac', ''),
                    worker.get('year', 0),
                )
            )
        print(line)

    else:
        print("Список пуст.")


def create_db(database_path: Path) -> None:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS name (
            name_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_title TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workers (
            worker_id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_name TEXT NOT NULL,
            name_id INTEGER NOT NULL,
            zodiac TEXT NOT NULL,
            worker_year INTEGER NOT NULL,
            FOREIGN KEY(name_id) REFERENCES name(name_id)
        )
        """
    )

    conn.close()


def add_worker(
        database_path: Path,
        surname: str,
        name: str,
        zodiac: str,
        year: int
) -> None:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name_id FROM name WHERE name_title = ?
        """,
        (name,)
    )
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            """
            INSERT INTO name (name_title) VALUES (?)
            """,
            (name,)
        )
        name_id = cursor.lastrowid

    else:
        name_id = row[0]

    cursor.execute(
        """
        INSERT INTO workers (worker_name, name_id, zodiac, worker_year)
        VALUES (?, ?, ?, ?)
        """,
        (surname, name_id, zodiac, year)
    )

    conn.commit()
    conn.close()


def select_all(database_path: Path) -> t.List[t.Dict[str, t.Any]]:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT workers.worker_name, name.name_title, workers.zodiac, 
        workers.worker_year
        FROM workers
        INNER JOIN name ON name.name_id = workers.name_id
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "surname": row[0],
            "name": row[1],
            "zodiac": row[2],
            "year": row[3],
        }
        for row in rows
    ]


def select_by_period(
        database_path: Path, period: int
) -> t.List[t.Dict[str, t.Any]]:
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT workers.worker_name, name.name_title, workers.zodiac,
        workers.worker_year\n
        FROM workers\n
        INNER JSON name ON names.name_id = workers.name_id\n
        WHERE (strftime('%Y', date('now')) - workers.worker_year) >= ?\n
        """,
        (period,)
    )
    rows = cursor.fetchall()

    conn.close()
    return [
        {
             "surname": row[0],
             "name": row[1],
             "zodiac": row[2],
             "year": row[3],
        }
        for row in rows
    ]


def main(command_line=None):
    file_parser = argparse.ArgumentParser(add_help=False)
    file_parser.add_argument(
        "--db",
        action="store",
        required=False,
        default=str(Path.home() / "workers.db"),
        help="The database file name"
    )

    parser = argparse.ArgumentParser("workers")
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    subparsers = parser.add_subparsers(dest="command")

    add = subparsers.add_parser(
        "add",
        parents=[file_parser],
        help="Add a new worker"
    )
    add.add_argument(
        "-s",
        "--surname",
        action="store",
        required=True,
        help="The worker`s surname"
    )
    add.add_argument(
        "-n",
        "--name",
        action="store",
        required=True,
        help="The worker`s name"
    )
    add.add_argument(
        "-z",
        "--zodiac",
        action="store",
        required=True,
        help="The year of zodiac"
    )
    add.add_argument(
        "-y",
        "--year",
        action="store",
        type=int,
        required=True,
        help="The year of date_obj"
    )

    _ = subparsers.add_parser(
        "display",
        parents=[file_parser],
        help="Display all workers"
    )

    select = subparsers.add_parser(
        "select",
        parents=[file_parser],
        help="Select the workers"
    )
    select.add_argument(
        "-P",
        "--period",
        action="store",
        type=int,
        required=True,
        help="The required period"
    )

    args = parser.parse_args(command_line)
    db_path = Path(args.db)
    create_db(db_path)

    if args.command == "add":
        add_worker(db_path, args.surname, args.name, args.zodiac, args.year)

    elif args.command == "display":
        display_workers(select_all(db_path))

    elif args.command == "select":
        display_workers(select_by_period(db_path, args.period))
        pass


if __name__ == "__main__":
    main()
