import copy


class MockingbirdDbConnection:
    """
    A class for handling database connections for different platforms such as Postgres, MS SQL, and MySQL.
    """

    SUPPORTED_PLATFORMS = ["postgres", "mssql", "mysql"]

    def __init__(self, platform: str, connection_type: str, url: str, arguments: dict):
        """
        Initializes the MockingbirdDbConnection object with the given platform, connection type, URL, and arguments.

        @param platform: The database platform (postgres, mssql, or mysql).
        @param connection_type: The type of connection ('url' or 'arguments').
        @param url: The URL for the database connection (if connection_type is 'url').
        @param arguments: The dictionary containing the connection arguments (if connection_type is 'arguments').
        """
        assert platform in MockingbirdDbConnection.SUPPORTED_PLATFORMS, f"Invalid db platform: {platform}"
        self.__conn = None

        self._platform = platform
        self._connection_type = connection_type
        self._arguments = arguments
        self._url = url

    @property
    def __connection_obj(self):
        """
        Returns the appropriate database connection object based on the platform and connection type.

        @return: The database connection object.
        """
        if self._connection_type == 'url':
            if self._platform == 'postgres':
                import psycopg2
                return psycopg2.connect(self._url)
            elif self._platform == 'mssql':
                import pyodbc
                return pyodbc.connect(self._url)
        elif self._connection_type == 'arguments':
            if self._platform == 'postgres':
                import psycopg2
                return psycopg2.connect(**self._arguments)
            elif self._platform == 'mssql':
                import pyodbc
                return pyodbc.connect(**self._arguments)
            elif self._platform == 'mysql':
                import mysql.connector
                # mysql args slightly dif
                args = copy.copy(self._arguments)
                args["database"] = args.pop('dbname')
                return mysql.connector.connect(**args)
        return None

    def delete_table(self, table_name: str):
        """
        Deletes a table in the database.

        @param table_name: The name of the table to be deleted.
        """
        cur = self.__conn.cursor()
        cur.execute(f"DROP TABLE {table_name}")
        self.__conn.commit()
        cur.close()

    def check_if_table_exists(self, table_name: str) -> int:
        """
        Checks if a table exists in the database and returns the row count if it does.

        @param table_name: The name of the table to check.
        @return: -1 if the table does not exist, otherwise the row count in the table.
        """
        # create connection and cursor
        exists = False
        cur = self.__conn.cursor()
        if self._platform == 'postgres':
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                        (table_name,))
            exists = cur.fetchone()[0]
        elif self._platform == 'mssql':
            cur.execute("SELECT * FROM sys.tables WHERE name = '{0}'".format(table_name))
            exists = cur.fetchone()
        elif self._platform == 'mysql':
            cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s",
                        (table_name,))
            exists = cur.fetchone()[0] == 1

        if exists:
            # get row count
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            # close connection and cursor
            row_count = cur.fetchone()[0]
            cur.close()
            self.__conn.commit()
            return row_count
        else:
            # close connection and cursor
            cur.close()
            self.__conn.commit()
            return -1

    @property
    def conn(self):
        assert self.__conn is not None, "conn is None!"
        return self.__conn

    @property
    def platform(self):
        return self._platform

    def connect(self) -> None:
        connection_obj = self.__connection_obj

        assert connection_obj is not None, f"No connection made with {self._platform}"
        self.__conn = connection_obj

    def close(self):
        self.__conn.close()
