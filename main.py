#!/opt/homebrew/bin/python3
import sqlite3
import sys
import os
from datetime import datetime

DB_FILE = str(os.getenv("HOME"))+'/.cache/pstimetrack.db'

def adapt_datetime(ts):
    return ts.isoformat(' ')

def convert_datetime(ts):
    try:
        return datetime.strptime(ts.decode('utf-8'), "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime.strptime(ts.decode('utf-8'), "%Y-%m-%d %H:%M:%S")

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("DATETIME", convert_datetime)

def create_project(conn, project_name):
    try:
        with conn:
            conn.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
        print(f"Project '{project_name}' created.")
    except sqlite3.IntegrityError:
        print(f"Project '{project_name}' already exists.")

def start_project(conn, project_name):
    project = conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,)).fetchone()
    if not project:
        print(f"Project '{project_name}' does not exist.")
        return

    # Stop any ongoing entries
    stop_project(conn, nomessage=True)

    with conn:
        conn.execute("INSERT INTO time_entries (project_id, start_time) VALUES (?, ?)",
                     (project[0], datetime.now()))
    print(f"Tracking started for project '{project_name}'.")

def stop_project(conn, nomessage=False):
    active_entry = conn.execute("SELECT id FROM time_entries WHERE end_time IS NULL").fetchone()
    if active_entry:
        with conn:
            conn.execute("UPDATE time_entries SET end_time = ? WHERE id = ?",
                         (datetime.now(), active_entry[0]))
        print("Tracking stopped.")
    elif nomessage is False:
        print("No active tracking to stop.")

def get_status(conn):
    projects = conn.execute("SELECT id, name FROM projects").fetchall()
    now = datetime.now()

    for project in projects:
        total_time = conn.execute("""
            SELECT SUM((julianday(end_time) - julianday(start_time)) * 86400.0)
            FROM time_entries
            WHERE project_id = ? AND end_time IS NOT NULL
        """, (project[0],)).fetchone()[0] or 0

        today_time = conn.execute("""
            SELECT SUM((julianday(end_time) - julianday(start_time)) * 86400.0)
            FROM time_entries
            WHERE project_id = ? AND end_time IS NOT NULL AND date(start_time) = date(?)
        """, (project[0], now)).fetchone()[0] or 0

        hourstt, minutestt = divmod(total_time / 60, 60)
        hourstd, minutestd = divmod(today_time / 60, 60)
        print(f"Project {project[1]:12s} Today: {int(hourstd):02d}:{int(minutestd):02d}, Total time: {int(hourstt):02d}:{int(minutestt):02d},")

def get_time_worked_today(conn):
    now = datetime.now()
    today_time = conn.execute("""
        SELECT SUM((julianday(end_time) - julianday(start_time)) * 86400.0)
        FROM time_entries
        WHERE end_time IS NOT NULL AND date(start_time) = date(?)
    """, (now,)).fetchone()[0] or 0

    active_entry = conn.execute("""
        SELECT start_time
        FROM time_entries
        WHERE end_time IS NULL
    """).fetchone()
    
    if active_entry:
        active_start_time = active_entry[0]
        today_time += (now - active_start_time).total_seconds()

    hours, minutes = divmod(today_time / 60, 60)
    print(f"{int(hours):02d}:{int(minutes):02d}")

def current_project(conn):
    active_entry = conn.execute("""
        SELECT projects.name
        FROM time_entries
        JOIN projects ON time_entries.project_id = projects.id
        WHERE end_time IS NULL
    """).fetchone()
    if active_entry:
        print(f"{active_entry[0]}")
    else:
        print("---")

def main():
    if len(sys.argv) < 2:
        print("Usage: tracker <command> [<args>]")
        with sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as conn:
            get_status(conn)
        return

    command = sys.argv[1]

    with sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES) as conn:
        if command == 'create':
            if len(sys.argv) != 3:
                print("Usage: tracker create <project_name>")
                return
            create_project(conn, sys.argv[2])
        elif command == 'start':
            if len(sys.argv) != 3:
                print("Usage: tracker start <project_name>")
                return
            start_project(conn, sys.argv[2])
        elif command == 'stop':
            stop_project(conn)
        elif command == 'status':
            get_status(conn)
        elif command == 'worked_today':
            get_time_worked_today(conn)
        elif command == 'current':
            current_project(conn)
        else:
            print(f"Unknown command: {command}")

if __name__ == '__main__':
    main()

