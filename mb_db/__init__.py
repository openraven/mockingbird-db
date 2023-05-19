import multiprocessing
from pathlib import Path

import yaml

from mb_db.mb_db_connection import MockingbirdDbConnection
from mb_db.mb_db_table import MockingbirdDBTable
from mb_db.mb_db_table_tracker import MockingbirdDBTableTrackerWriter


class MockingbirdDB:
    """
    A class representing a Mockingbird database, responsible for processing and populating tables based on the
    provided configuration.
    """

    def __init__(self, config_path: Path, rows_written=None):
        """
        Initializes the MockingbirdDB object with the given configuration file path and rows_written object.

        @param config_path: A pathlib.Path object representing the configuration file path.
        @param rows_written: An optional object to track the number of rows written (default: None).
        """

        self._rows_written = rows_written
        with open(config_path) as f:
            self._config = yaml.safe_load(f)

        self._tables = self._config['tables']
        manager = multiprocessing.Manager()
        self._table_tracker = manager.dict()

    def process(self, populate_async=None):
        """
        Processes and populates the tables defined in the configuration file.

        @param populate_async: An optional boolean to indicate if the table population should be done asynchronously (default: None).
        """
        for table_config in self._tables:
            table_config = MockingbirdDBTable(table_config=table_config,
                                              rows_written=self._rows_written,
                                              db_info=self._config['db_info'],
                                              table_tracker=self._table_tracker)
            table_config.connect()
            table_config.populate_table(populate_async=populate_async)
            table_config.close()

    def dump_metadata(self, metadata_path: Path):
        """
        Dumps the metadata for all tables to a specified file.

        @param metadata_path: The output file path where metadata should be written.
        """
        mb_db_tb_writer = MockingbirdDBTableTrackerWriter(self._table_tracker)
        metadata = mb_db_tb_writer.create_metadata()

        with metadata_path.open('w') as metadata_file:
            yaml.dump(metadata, metadata_file, indent=4, sort_keys=True)
