import logging
import re

from sqlalchemy import (
    create_engine, text, inspect, MetaData,
    Table, select, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
from .models import NoAuthorizationError

# Configure module-level logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Database:
    """Database management class."""

    def __init__(self, db_url: str | None = None):
        """
        Initialize the Database instance.

        Args:
            db_url (str, optional): Connection URL; if None, uses settings.DATABASE_URL.
        """
        self.db_url = db_url or settings.DATABASE_URL
        self._init_db()

    def _init_db(self):
        """Establish database connection and session factory."""
        try:
            # Create SQLAlchemy engine
            self.engine = create_engine(self.db_url + "?client_encoding=utf8")
            # Configure session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            # Base class for declarative models
            self.Base = declarative_base()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def get_session(self):
        """
        Provide a database session.

        Yields:
            Session: SQLAlchemy session object.
        """
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def execute_query(self, query: str, params: dict | None = None) -> list[dict]:
        """
        Execute a SQL query and return the result as a list of dicts.
        Only SELECT queries are allowed. Attempts to run INSERT, UPDATE,
        DELETE, or DROP will raise NoAuthorizationError.

        Args:
            query (str): SQL query string.
            params (dict, optional): Parameters for a parameterized query.

        Returns:
            List[dict]: Each row as a dict of column->value.

        Raises:
            NoAuthorizationError: If a forbidden SQL keyword is detected.
            Exception: For any other execution error.
        """
        # Forbidden SQL keywords
        forbidden_patterns = [
            r"\bINSERT\b",
            r"\bUPDATE\b",
            r"\bDELETE\b",
            r"\bDROP\b",
        ]
        # Check for forbidden keywords (case-insensitive)
        for pattern in forbidden_patterns:
            if re.search(pattern, query, flags=re.IGNORECASE):
                logger.error(f"Forbidden SQL operation detected: {pattern}")
                # Raise with blocked query attached
                raise NoAuthorizationError(
                    query=query,
                    message="You are not authorized to perform write or schema-altering operations."
                )

        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))

                # If SELECT-like, fetch rows
                if result.returns_rows:
                    cols = result.keys()
                    return [dict(zip(cols, row)) for row in result.fetchall()]
                # Non-SELECT returns empty list
                return []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            if params:
                logger.error(f"Params: {params}")
            raise


class SchemaManager:
    """Database schema inspection and management class."""

    def __init__(self, database: Database):
        """
        Initialize SchemaManager with a Database instance.

        Args:
            database (Database): Initialized Database object.
        """
        self.engine = database.engine
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        # Reflect existing schema
        self.metadata.reflect(bind=self.engine)
        self._Session = sessionmaker(bind=self.engine)

    def get_tables(self) -> list[str]:
        """
        Get the list of all table names in the database.

        Returns:
            List[str]: Table names.
        """
        return self.inspector.get_table_names()

    def get_schema(self) -> dict:
        """
        Retrieve schema information for all tables.

        Returns:
            Dict[str, Any]: Mapping from table name to its columns,
            primary keys, foreign keys, and indices.
        """
        info: dict = {}
        for table in self.get_tables():
            cols = [{
                "name": c["name"],
                "type": str(c["type"]),
                "nullable": c.get("nullable", True),
                "default": str(c.get("default", "")),
            } for c in self.inspector.get_columns(table)]

            pk = self.inspector.get_pk_constraint(table).get("constrained_columns", [])
            fks = [{
                "constrained_columns": fk.get("constrained_columns", []),
                "referred_table": fk.get("referred_table", ""),
                "referred_columns": fk.get("referred_columns", []),
            } for fk in self.inspector.get_foreign_keys(table)]

            idxs = [{
                "name": idx.get("name", ""),
                "columns": idx.get("column_names", []),
                "unique": idx.get("unique", False),
            } for idx in self.inspector.get_indexes(table)]

            info[table] = {
                "columns": cols,
                "primary_keys": pk,
                "foreign_keys": fks,
                "indices": idxs,
            }
        return info

    def get_column_uniques(
        self,
        table_name: str,
        column_name: str,
        unique_threshold: int = 10
    ) -> dict:
        """
        Retrieve unique values or range for a single column.

        Args:
            table_name (str): Name of the table.
            column_name (str): Name of the column.
            unique_threshold (int): If unique count > threshold and numeric,
                                     return min/max; else list distinct values.

        Returns:
            Dict[str, Any]: {
                "type": <SQL type>,
                "unique_count": <int>,
                "values": <list|{"min":..., "max":...}>
            }
        """
        # Get column type from inspector metadata
        col_meta = next(
            c for c in self.inspector.get_columns(table_name)
            if c["name"] == column_name
        )
        dtype = str(col_meta["type"])

        with self.engine.connect() as conn:
            # count distinct
            unique_count = conn.execute(
                text(f"SELECT COUNT(DISTINCT \"{column_name}\") FROM {table_name}")
            ).scalar_one()

            # numeric types: int, float, numeric, decimal
            if unique_count > unique_threshold and re.match(r"^(INTEGER|FLOAT|NUMERIC|DECIMAL)", dtype, re.IGNORECASE):
                mn, mx = conn.execute(
                    text(f"SELECT MIN(\"{column_name}\"), MAX(\"{column_name}\") FROM {table_name}")
                ).one()
                values = {"min": mn, "max": mx}
            else:
                rows = conn.execute(
                    text(f"SELECT DISTINCT \"{column_name}\" FROM {table_name} LIMIT :lim"),
                    {"lim": unique_threshold}
                ).fetchall()
                values = [r[0] for r in rows]

        return {
            "type": dtype,
            "unique_count": unique_count,
            "values": values
        }

    def get_all_columns_uniques(
        self,
        table_name: str,
        unique_threshold: int = 10
    ) -> dict:
        """
        Retrieve unique info for all columns in a table.

        Args:
            table_name (str): Name of the table.
            unique_threshold (int): Threshold for numeric vs categorical handling.

        Returns:
            Dict[str, dict]: Mapping column->unique info dict.
        """
        uniques: dict = {}
        # Loop through each column and reuse get_column_uniques
        for col in [c["name"] for c in self.inspector.get_columns(table_name)]:
            uniques[col] = self.get_column_uniques(
                table_name=table_name,
                column_name=col,
                unique_threshold=unique_threshold
            )
        return uniques

    def get_table_summary(self, table_name: str) -> dict:
        """
        Generate basic summary statistics for all columns.

        - Numeric columns: count, mean, stddev_pop, min, max
        - Non-numeric: count, unique_count, top value, top frequency

        Args:
            table_name (str): Name of the table.

        Returns:
            Dict[str, dict]: Mapping column->summary stats.
        """
        summary: dict = {}
        table = Table(table_name, self.metadata, autoload_with=self.engine)

        with self._Session() as session:
            total_rows = session.execute(select(func.count()).select_from(table)).scalar_one()

            for col in table.c:
                col_name = col.name
                col_type = str(col.type)
                is_numeric = col.type.python_type in (int, float)

                if is_numeric:
                    cnt, mean, sd, mn, mx = session.execute(
                        select(
                            func.count(col),
                            func.avg(col),
                            func.stddev_pop(col),
                            func.min(col),
                            func.max(col)
                        )
                    ).one()
                    summary[col_name] = {
                        "type":      col_type,
                        "count":     cnt,
                        "mean":      float(mean or 0),
                        "stddev":    float(sd or 0),
                        "min":       mn,
                        "max":       mx,
                    }
                else:
                    uq = session.execute(
                        select(func.count(func.distinct(col)))
                    ).scalar_one()
                    top_row = session.execute(
                        select(col, func.count().label("freq"))
                        .group_by(col)
                        .order_by(func.count().desc())
                        .limit(1)
                    ).one_or_none()
                    top_val, top_freq = top_row if top_row else (None, 0)
                    summary[col_name] = {
                        "type":         col_type,
                        "count":        total_rows,
                        "unique_count": uq,
                        "top":          top_val,
                        "top_freq":     top_freq
                    }

        return summary


# Instantiate the database and schema manager
db = Database()
schema_manager = SchemaManager(database=db)
