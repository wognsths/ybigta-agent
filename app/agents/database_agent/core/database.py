from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging
from sqlalchemy import inspect, MetaData

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Database:
    """Database management class"""

    def __init__(self, db_url=None):
        self.db_url = db_url or settings.DATABASE_URL
        self.engine = None
        self.SessionLocal = None
        self.init_db()

    def init_db(self):
        """Initalize database"""
        try:
            self.engine = create_engine(self.db_url)
            self.SessionLocal = sessionmaker(autocommit = False,
                                             autoflush  = False,
                                             bind       = self.engine)
            self.Base = declarative_base()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def get_session(self):
        """Return database session"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def execute_query(self, query, params = None):
        """
        Execute SQL query

        Args:
            query: SQL query string
            params: (Optional) Query parameter
        Returns:
            Query result (Dictionary list)
        """
        try:
            with self.engine.connect() as connection:
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
            
                if result.returns_rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in result.fetchall()]
                return []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            if params:
                logger.error(f"Params: {params}")
            raise

class SchemaManager:
    """Database schema managing class"""
    
    def __init__(self, database: Database):
        self.engine = database.engine
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
    
    def get_tables(self):
        """Check table list"""
        return self.inspector.get_table_names()
    
    def get_schema(self):
        """
        Check database schema info

        Returns:
            Dictionary containing information of table, column, relation
        """

        schema_info = {}
        tables = self.get_tables()

        for table in tables:
            # Column info
            columns = []
            for column in self.inspector.get_columns(table):
                columns.append({
                    "name"    : column["name"],
                    "type"    : str(column["type"]),
                    "nullable": column.get("nullable", True),
                    "default" : str(column.get("default", ""))
                })
            # Primary key
            pk = self.inspector.get_pk_constraint(table)
            primary_keys = pk.get("constrained_columns", [])

            # Foreign key
            foreign_keys = []
            for fk in self.inspector.get_foreign_keys(table):
                foreign_keys.append({
                    "constrained_columns": fk.get("constrained_columns", []),
                    "referred_table"     : fk.get("referred_table", ""),
                    "referred_columns"   : fk.get("referred_columns", [])
                })

            # Index
            indices = []
            for index in self.inspector.get_indexes(table):
                indices.append({
                    "name"   : index.get("name", ""),
                    "columns": index.get("column_names", []),
                    "unique" : index.get("unique", False)
                })

            # Add table info
            schema_info[table] = {
                "columns"     : columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
                "indices"     : indices
            }
        return schema_info
    
    def get_schema_as_string(self):
        """
        Convert database schema into string format

        Returns:
            str: Schema information
        """
        schema = self.get_schema()
        result = []

        for table_name, table_info in schema.items():
            table_str = f"Table: {table_name}\n"

            # Column info
            table_str += "Columns:\n"
            for col in table_info["columns"]:
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                default  = f"DEFAULT {col['default']}" if col["default"] != "None" else ""
                primary  = "PRIMARY KEY" if col["name"] in table_info["primary_keys"] else ""

                table_str += f"  - {col['name']} {col['type']} {nullable} {default} {primary}\n"

            # Foreign key info
            if table_info["foreign_keys"]:
                table_str += "Foreign Keys: \n"
                for fk in table_info["foreign_keys"]:
                    table_str += f"  - {', '.join(fk['constrained_columns'])} REFERENCES {fk['referred_table']}({', '.join(fk['referred_columns'])})\n"
            
            result.append(table_str)

        return "\n".join(result)
    
    def get_table_sample_data(self, table_name, limit=5):
        """
        Check sample data of table

        Args:
            table_name: name of table
            limit: max row number to check
        
        Returns:
            list: sample data
        """
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        try:
            return db.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get sample data for table {table_name}: {e}")
            return []
        
db = Database()
schema_manager = SchemaManager(database=db)