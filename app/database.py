# app/database.py - Database Connection Handler - PROFESSIONAL VERSION

import pyodbc
from contextlib import contextmanager
import logging

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Database connection manager for SQL Server
    Handles all database operations with proper error handling and resource management
    """
    
    # Database Configuration
    SERVER = 'khaled_win'
    DATABASE = 'ITI_Examination_System'
    DRIVER = 'ODBC Driver 17 for SQL Server'
    
    @classmethod
    def get_connection_string(cls):
        """Generate connection string"""
        return f'''
        DRIVER={{{cls.DRIVER}}};
        SERVER={cls.SERVER};
        DATABASE={cls.DATABASE};
        Trusted_Connection=yes;
        '''
    
    @staticmethod
    def get_connection():
        """
        Get a new database connection
        
        Returns:
            pyodbc.Connection: Database connection object
            
        Raises:
            Exception: If connection fails
        """
        try:
            connection = pyodbc.connect(DatabaseConnection.get_connection_string())
            return connection
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    @staticmethod
    @contextmanager
    def get_cursor():
        """
        Context manager for database cursor
        Automatically commits on success, rolls back on error
        
        Yields:
            pyodbc.Cursor: Database cursor
        """
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {str(e)}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def execute_query(query, params=None):
        """
        Execute INSERT, UPDATE, or DELETE query
        
        Args:
            query (str): SQL query to execute
            params (tuple): Query parameters
            
        Returns:
            int: Number of affected rows
        """
        with DatabaseConnection.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    @staticmethod
    def fetch_all(query, params=None):
        """
        Fetch all rows from SELECT query
        
        Args:
            query (str): SQL SELECT query
            params (tuple): Query parameters
            
        Returns:
            list: List of tuples containing rows
        """
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            logger.error(f"Fetch all query failed: {str(e)}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def fetch_one(query, params=None):
        """
        Fetch single row from SELECT query
        
        Args:
            query (str): SQL SELECT query
            params (tuple): Query parameters
            
        Returns:
            tuple: Single row or None
        """
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return result
        except Exception as e:
            logger.error(f"Fetch one query failed: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def execute_scalar(query, params=None):
        """
        Execute query and return single scalar value
        Useful for COUNT, MAX, or SCOPE_IDENTITY()
        
        Args:
            query (str): SQL query
            params (tuple): Query parameters
            
        Returns:
            Value or None
        """
        result = DatabaseConnection.fetch_one(query, params)
        return result[0] if result else None
    
    @staticmethod
    def get_last_insert_id():
        """
        Get the last inserted identity value
        Uses SCOPE_IDENTITY() for SQL Server
        
        Returns:
            int: Last inserted ID
        """
        return DatabaseConnection.execute_scalar("SELECT CAST(SCOPE_IDENTITY() AS INT)")
