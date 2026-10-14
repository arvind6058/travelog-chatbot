"""
Minimal, additive schema migration for existing databases.

``Base.metadata.create_all`` never emits ``ALTER TABLE``, so a database created
before a column was declared keeps the old shape and every query against the new
column fails at runtime. This module adds the missing columns and indexes in
place. It is deliberately additive only (no drops, no type changes) so it can
run unattended on startup; anything beyond that needs a real migration tool.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, Numeric, inspect, text
from sqlalchemy.schema import CreateIndex

from app.core.logging import logger
from app.db.base import Base


def _default_literal(column) -> Optional[str]:
    """A constant SQL default usable by ALTER TABLE ... ADD COLUMN."""
    try:
        python_default = column.default.arg if column.default is not None else None
        if callable(python_default):
            python_default = None
    except Exception:
        python_default = None

    if python_default is not None and isinstance(python_default, (bool, int, float, str)):
        if isinstance(python_default, bool):
            return "1" if python_default else "0"
        if isinstance(python_default, (int, float)):
            return str(python_default)
        return "'" + str(python_default).replace("'", "''") + "'"

    if isinstance(column.type, Boolean):
        return "0"
    if isinstance(column.type, (Integer, Numeric, Float)):
        return "0"
    if isinstance(column.type, DateTime):
        # SQLite rejects CURRENT_TIMESTAMP as an ADD COLUMN default.
        return "'1970-01-01 00:00:00'"
    return "''"


def _add_missing_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    existing_tables = set(inspector.get_table_names())
    preparer = sync_conn.dialect.identifier_preparer

    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        present = {col["name"] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in present:
                continue
            try:
                ddl_type = column.type.compile(dialect=sync_conn.dialect)
            except Exception:
                logger.warning(f"Could not render a type for {table.name}.{column.name}; skipping.")
                continue

            statement = (
                f"ALTER TABLE {preparer.quote(table.name)} "
                f"ADD COLUMN {preparer.quote(column.name)} {ddl_type}"
            )
            if not column.nullable:
                default_sql = _default_literal(column)
                if default_sql is not None:
                    statement += f" DEFAULT {default_sql}"
                statement += " NOT NULL"

            try:
                sync_conn.exec_driver_sql(statement)
                logger.info(f"Schema update: added {table.name}.{column.name}")
            except Exception as exc:
                logger.warning(f"Could not add column {table.name}.{column.name}: {exc}")


def _create_missing_indexes(sync_conn) -> None:
    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            try:
                if index.name in {ix["name"] for ix in inspect(sync_conn).get_indexes(table.name)}:
                    continue
            except Exception:
                pass
            try:
                sync_conn.execute(CreateIndex(index, if_not_exists=True))
                logger.info(f"Schema update: created index {index.name}")
            except Exception as exc:
                logger.warning(f"Could not create index {index.name}: {exc}")


def apply_schema_updates(sync_conn) -> None:
    """Additive-only migration entry point (called via run_sync)."""
    _add_missing_columns(sync_conn)
    _create_missing_indexes(sync_conn)


__all__ = ["apply_schema_updates"]
