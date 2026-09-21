"""Startup guard: verifies the database on disk actually matches the SQLAlchemy
models, not just that a migration ran at some point.

The specific failure this exists for: a SQLite file left over from an earlier
version of the app -- created before a column or table was added -- looks
completely fine to a check that only confirms the expected *tables* exist. The
first request that touches the missing column then fails with a raw
OperationalError from deep inside a query, which is what actually happened here:
`no such column: issues.needs_triage` on a database that predated that column.

Comparing every modeled table's expected columns against what is actually on disk
catches that at startup, with the exact table and column named, instead of at
request time with a stack trace.
"""

from typing import Dict, List, Set

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.schema import MetaData


def missing_required_tables(engine: Engine, required_tables: Set[str]) -> Set[str]:
    """Required table names that do not exist on disk at all."""
    existing = set(inspect(engine).get_table_names())
    return required_tables - existing


def missing_columns_by_table(engine: Engine, metadata: MetaData) -> Dict[str, List[str]]:
    """For every modeled table that exists on disk, the columns the model expects
    but the table does not have. Only checks tables that exist -- a table missing
    entirely is `missing_required_tables`'s job, not this one's."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    gaps: Dict[str, List[str]] = {}
    for table_name, table in metadata.tables.items():
        if table_name not in existing_tables:
            continue
        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        expected_columns = {column.name for column in table.columns}
        missing = expected_columns - actual_columns
        if missing:
            gaps[table_name] = sorted(missing)

    return gaps


def format_missing_tables_error(missing_tables: Set[str]) -> str:
    return (
        f"Database is missing tables: {', '.join(sorted(missing_tables))}. "
        "Run 'alembic upgrade head' before starting the API."
    )


def format_missing_columns_error(missing_columns: Dict[str, List[str]]) -> str:
    detail = "; ".join(f"{table} missing {columns}" for table, columns in missing_columns.items())
    return (
        f"Database schema is out of date: {detail}. The database on disk was "
        "likely created before a migration was added. Run 'alembic upgrade head' "
        "to bring it current, or, for a development database you don't need to "
        "keep, delete the file and run 'alembic upgrade head' again to rebuild it "
        "from scratch."
    )
