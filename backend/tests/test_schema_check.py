"""Pins the exact failure a stale database file causes: a table exists but is
missing a column a later migration added, and the app should refuse to start
with a clear message instead of failing inside the first request that touches
that column."""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from app.database import Base
from app.schema_check import (
    format_missing_columns_error,
    format_missing_tables_error,
    missing_columns_by_table,
    missing_required_tables,
)


@pytest.fixture
def scratch_engine():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "scratch.db"
        engine = create_engine(f"sqlite:///{db_path}")
        yield engine
        engine.dispose()


def test_a_fully_migrated_database_reports_nothing_missing(scratch_engine):
    Base.metadata.create_all(scratch_engine)

    assert missing_required_tables(scratch_engine, {"users", "issues"}) == set()
    assert missing_columns_by_table(scratch_engine, Base.metadata) == {}


def test_a_table_missing_entirely_is_reported(scratch_engine):
    # Nothing created at all: every required table is missing.
    missing = missing_required_tables(scratch_engine, {"users", "issues", "reports"})

    assert missing == {"users", "issues", "reports"}
    assert "alembic upgrade head" in format_missing_tables_error(missing)


def test_a_table_missing_a_column_added_by_a_later_migration_is_reported(scratch_engine):
    """Reproduces the reported bug directly: an 'issues' table that predates the
    needs_triage column, exactly like a pre-existing SQLite file would have."""
    stale_metadata = MetaData()
    Table(
        "issues",
        stale_metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(255), nullable=False),
        # needs_triage, and everything else added after the first version of this
        # table, is deliberately absent here.
    )
    stale_metadata.create_all(scratch_engine)

    gaps = missing_columns_by_table(scratch_engine, Base.metadata)

    assert "issues" in gaps
    assert "needs_triage" in gaps["issues"]

    message = format_missing_columns_error(gaps)
    assert "issues" in message
    assert "needs_triage" in message
    assert "alembic upgrade head" in message


def test_a_table_not_touched_by_the_models_is_ignored(scratch_engine):
    """A table the app doesn't know about (a leftover from something else
    entirely) is not this check's business."""
    stale_metadata = MetaData()
    Table("some_other_apps_table", stale_metadata, Column("id", Integer, primary_key=True))
    stale_metadata.create_all(scratch_engine)

    assert missing_columns_by_table(scratch_engine, Base.metadata) == {}
