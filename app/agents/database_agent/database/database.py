import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    create_engine, text, inspect, MetaData,
    Table, select, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .config import settings


class NoAuthorizationError(Exception):
    """Raised when a non‑read‑only statement is detected."""

    def __init__(self, query: str, message: str | None = None):
        msg = message or "Forbidden SQL operation attempted."
        super().__init__(f"{msg}\nBlocked query: {query}")
        self.query = query


# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# ──────────────────────────────────────────────────────────────
# Database core
# ──────────────────────────────────────────────────────────────
class Database:
    """Light wrapper around SQLAlchemy Engine / Session factory."""

    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or settings.DATABASE_URL
        self._init_db()

    def _init_db(self) -> None:
        """Create engine + session factory."""
        self.engine = create_engine(f"{self.db_url}?client_encoding=utf8")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()
        logger.info("Database connection established")

    # context‑managed generator
    def get_session(self):
        db: Session = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    _FORBIDDEN_RE = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE)\b", re.I)

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if self._FORBIDDEN_RE.search(query):
            raise NoAuthorizationError(query)
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            if result.returns_rows:
                cols = result.keys()
                return [dict(zip(cols, row)) for row in result.fetchall()]
            return []


# ──────────────────────────────────────────────────────────────
# Schema inspection helpers
# ──────────────────────────────────────────────────────────────
class SchemaManager:
    def __init__(self, database: Database):
        self.engine = database.engine
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self._Session = sessionmaker(bind=self.engine)

    # ---------------------------------------------------------
    # Basic table / column info
    # ---------------------------------------------------------
    def get_tables(self) -> List[str]:
        return self.inspector.get_table_names()

    def get_schema(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for tbl in self.get_tables():
            cols = self.inspector.get_columns(tbl)
            out[tbl] = {
                "columns": [
                    {
                        "name": c["name"],
                        "type": str(c["type"]),
                        "nullable": c.get("nullable", True),
                        "default": str(c.get("default")) if c.get("default") else None,
                    } for c in cols
                ],
                "primary_keys": self.inspector.get_pk_constraint(tbl).get("constrained_columns", []),
                "foreign_keys": self.inspector.get_foreign_keys(tbl),
                "indices": self.inspector.get_indexes(tbl),
            }
        return out

    # ---------------------------------------------------------
    # Unique values or numeric range for a single column
    # ---------------------------------------------------------
    _NUMERIC_RE = re.compile(r"^(NUMERIC|DECIMAL|INTEGER|FLOAT|REAL|DOUBLE|SMALLINT|BIGINT)", re.I)

    def _is_numeric(self, sql_type: str) -> bool:
        return bool(self._NUMERIC_RE.match(sql_type))

    # ---------------------------------------------------------
    # Summary stats for entire table
    # ---------------------------------------------------------
    def get_table_summary(self, table: str) -> Dict[str, Any]:
        tbl = Table(table, self.metadata, autoload_with=self.engine)
        summary: Dict[str, Any] = {}
        with self._Session() as ses:
            total_rows = ses.execute(select(func.count()).select_from(tbl)).scalar_one()

            for col in tbl.c:
                c_name = col.name
                c_type = str(col.type)
                py_type = getattr(col.type, "python_type", str)
                is_num = py_type in (int, float)

                if is_num:
                    cnt, mean, sd, mn, mx = ses.execute(
                        select(
                            func.count(col), func.avg(col), func.stddev_pop(col), func.min(col), func.max(col)
                        )
                    ).one()
                    summary[c_name] = {
                        "type": c_type,
                        "count": cnt,
                        "mean": float(mean or 0),
                        "stddev": float(sd or 0),
                        "min": mn,
                        "max": mx,
                    }
                else:
                    uniq_cnt = ses.execute(select(func.count(func.distinct(col)))).scalar_one()
                    top_val, top_freq = ses.execute(
                        select(col, func.count().label("freq")).group_by(col).order_by(func.count().desc()).limit(1)
                    ).one_or_none() or (None, 0)
                    summary[c_name] = {
                        "type": c_type,
                        "count": total_rows,
                        "unique_count": uniq_cnt,
                        "top": top_val,
                        "top_freq": top_freq,
                    }
        return summary

    # ---------------------------------------------------------
    # Sample rows helper
    # ---------------------------------------------------------
    def get_table_sample_data(self, table: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            return db.execute_query(f'SELECT * FROM "{table}" LIMIT {limit}')
        except Exception as exc:
            logger.error("Failed to fetch sample data", exc_info=exc)
            return []


# ──────────────────────────────────────────────────────────────
# Global instances
# ──────────────────────────────────────────────────────────────

db = Database()
schema_manager = SchemaManager(db)
