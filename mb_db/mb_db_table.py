import multiprocessing
import logging
import sys
from typing import List, Dict

import numpy as np

from mb_db.mb_db_column import MockingbirdDbColumn
from mb_db.mb_db_connection import MockingbirdDbConnection
from mb_db.mb_db_table_tracker import MockingbirdDBTableTracker

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)


def prompt_confirmation():
    while True:
        confirmation = input("Are you sure you want to proceed? (yes/no): ")
        if confirmation.lower() == 'yes':
            return True
        elif confirmation.lower() == 'no':
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")


class MockingbirdDBTable:
    """
    The MockingbirdDBTable class represents a table in the Mockingbird database. It handles tasks such as creating the
    table schema, generating rows to insert, and populating the table with data. This class also supports populating
    the table asynchronously using multiple processes.
    """
    def __init__(self,
                 table_config: dict,
                 rows_written,
                 db_info: dict,
                 table_tracker: dict):
        self._config_path = table_config
        self._rows_written = rows_written

        self._table_config = table_config
        self._rows = self._table_config['rows']
        self._table_name = self._table_config['table_name']

        self._table_tracker = table_tracker
        self._mb_db_connection = MockingbirdDbConnection(**db_info)
        self._db_info = db_info
        self._columns = self._construct_columns_from_config()

    @staticmethod
    def __generate_array_sum_n(N, K):
        """
        Generate an array of K elements, such that sum(k) = N,
        and each element K_i is equal to K_i+1, for some i, except
        for the last element, which may be smaller than K in order
        to compensate for a situation where K doesn't divide N evenly.
        """
        quotient, remainder = divmod(N, K)
        arr = [quotient] * K
        if remainder > 0:
            arr[-1] = quotient + remainder
        return arr

    def populate_table(self, populate_async=1):
        """
        Populates the table with data.
        If populate_async is provided, the table will be populated asynchronously using the given number of processes.

        @param populate_async: Number of processes to use for populating the table asynchronously.
        """
        row_count = self._mb_db_connection.check_if_table_exists(self._table_name)

        if row_count != -1:
            logger.warning(f"You are about to delete {row_count} rows in the table '{self._table_name}'.")
            confirmation = prompt_confirmation()

            if confirmation:
                self._mb_db_connection.delete_table(self._table_name)
                logger.info("Table deleted successfully.")
            else:
                logger.info("Table deletion cancelled.")
                sys.exit(0)

        conn = self._mb_db_connection.conn
        cur = conn.cursor()
        cur.execute(self._create_table_statement())
        conn.commit()

        cur.close()
        conn.close()

        if populate_async != 1:
            batched_rows = self.__generate_array_sum_n(self._rows, populate_async)

            # Use multiprocessing to call _populate_table_threaded on each batch of rows.
            with multiprocessing.Pool(populate_async) as pool:
                pool.starmap(self._populate_table_threaded,
                             [(pid,
                               batch,
                               self._columns,
                               self._table_name,
                               self._db_info,
                               self._table_tracker,
                               self._rows_written) for pid, batch in enumerate(batched_rows)])

        else:
            # Call using a non-multiprocess approach. Useful for debugging.
            self._populate_table_threaded(0,
                                          self._rows,
                                          self._columns,
                                          self._table_name,
                                          self._db_info,
                                          self._table_tracker,
                                          self._rows_written)

    @staticmethod
    def _populate_table_threaded(pid: int,
                                 rows_count: int,
                                 columns: List[MockingbirdDbColumn],
                                 table_name: str,
                                 db_info: dict,
                                 table_tracker: dict,
                                 rows_written_shared) -> None:
        """
        Static method used by multiprocessing to populate the table in parallel.

        @param pid: Process ID. This helps to ensure each process updates its own unique count key when this function
                    is being executed in a multiprocess environment.
        @param rows_count: How many rows this thread is supposed to populate.
        @param table_name: Name of the table to populate.
        @param db_info: Database connection information.
        @param rows_written_shared: Shared memory value used for tracking the number of rows written by all processes.
        """
        mb_db_connection = MockingbirdDbConnection(**db_info)
        mb_db_connection.connect()
        conn = mb_db_connection.conn
        cur = conn.cursor()

        sample_row = MockingbirdDBTable.__get_row(columns)
        insert, values = MockingbirdDBTable.__create_insert(table_name, [sample_row])
        values_appender = ''
        rows_written = 0

        for i in range(rows_count):
            row = MockingbirdDBTable.__get_row(columns, pid, table_tracker)
            if values_appender == '':
                values_appender = values.format(*list(row.values()))
            else:
                values_appender = values_appender + ',' + values.format(*list(row.values()))

            # Replace none values with NULL for insertion
            values_appender = values_appender.replace("'None'", "NULL")
            rows_written += 1

            if (i + 1) % 500 == 0:
                cur.execute(insert + values_appender)
                values_appender = ''
                conn.commit()
                if rows_written_shared:
                    rows_written_shared.value += rows_written
                rows_written = 0

        if values_appender != '':
            cur.execute(insert + values_appender)
            conn.commit()

            if rows_written_shared:
                rows_written_shared.value += rows_written

        cur.close()
        mb_db_connection.close()

    @staticmethod
    def __get_row(columns: List[MockingbirdDbColumn], pid: int = 0, table_tracker: dict = None) -> Dict[str, str]:
        """
        Generates a dictionary representing a single row to insert into the table based on the provided columns.

        The Process ID (pid) is necessary here because this function may be executed in parallel across multiple
        processes. Without the pid, if two processes are attempting to increment the count for the same column at the
        same time, it might result in incorrect count values due to race conditions. With pid included in the key,
        each process increments its own unique key, thus avoiding these potential issues.

        @param columns: List of MockingbirdDbColumn objects.
        @param pid: Process ID. This helps to ensure each process updates its own unique count key when this function
                    is being executed in a multiprocess environment.
        @param table_tracker: A dictionary for tracking the count of dataclass in each column.
        @return: Dictionary containing the data for a single row to insert into the table.
        """
        row = {}
        for column in columns:
            # Call get_field for each column. Pass the pid and table_tracker so that get_field can track
            # the counts correctly for this process.
            row.update(column.get_field(pid=pid, table_tracker=table_tracker))

        return row

    def _construct_columns_from_config(self) -> List[MockingbirdDbColumn]:
        """
        Constructs columns based on the provided table configuration.

        @return: List of MockingbirdDbColumn objects.
        """
        columns = []

        for col in self._table_config['columns']:
            col.update({"platform": self._mb_db_connection.platform})
            col.update({"table_name": self._table_name})
            col = MockingbirdDbColumn(**col)
            columns.append(col)

        return columns

    def connect(self):
        """
        Connects to the database.
        """
        self._mb_db_connection.connect()

    def close(self):
        """
        Closes the database connection.
        """
        self._mb_db_connection.close()

    def _create_table_statement(self):
        """
        Generates a CREATE TABLE statement for the current table and the made columns.
        @return: SQL string for creating the table.
        """

        jsonb_supported = self._mb_db_connection.platform == 'postgres'
        make_table = f"CREATE TABLE {self._table_name} ("

        for column in self._columns:
            make_table += f"{column.column_name} "

            if column.column_type == "json":
                if jsonb_supported:
                    make_table += "JSONB,"
                else:  # Jsonb is only supported in postgres. Mysql and Mssql use varchar columns.
                    print(f'Column {column.column_name} was defined as JSON but the underlying platform '
                          f'{self._mb_db_connection.platform} does not support JSON columns. Column will be written as VARCHAR.')
                    make_table += "VARCHAR(255),"
            elif column._column_type == "string":
                make_table += "VARCHAR(255),"

        make_table = make_table[:-1]
        make_table += ")"
        return make_table

    @staticmethod
    def __create_insert(table_name, rows: List[dict]):
        """
        Creates an INSERT statement for inserting rows into the table.

        @param table_name: Name of the table to insert rows into.
        @param rows: List of dictionaries containing the data to insert into the table.
        @return: Tuple containing the INSERT statement and the VALUES statement.
        """

        insert_statement = f"INSERT INTO {table_name} ("

        for key in rows[0].keys():
            insert_statement += f"{key}, "

        insert_statement = insert_statement[:-2] + ") VALUES "
        values_statement = "( "

        for _ in rows[0].keys():
            values_statement += "'{}', "

        values_statement = values_statement[:-2] + ")"
        return insert_statement, values_statement
