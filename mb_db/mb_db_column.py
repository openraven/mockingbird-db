import json
import random
from typing import Dict, Union, List

from mb_db.mb_datasource import MbDataSource
from mb_db.mb_db_table_tracker import MockingbirdDBTableTracker
from mb_db.table_utils import to_sql_column_name


class MockingbirdDbColumn:
    """
    A class representing a column in a Mockingbird database, handling the generation of random data for the column.
    """

    def __init__(self,
                 table_name: str,
                 column_name: str,
                 platform: str,
                 datasources: List[Dict[str, Union[str, float]]],
                 nested_json_name: str,
                 column_type: str):
        """
        Initializes the MockingbirdDbColumn object with the given parameters.

        @param column_name: The name of the column.
        @param platform: The database platform (postgres, mssql, or mysql).
        @param datasources: A list of dictionaries containing data sources and their corresponding probabilities.
        @param nested_json_name: The name to be used if the column type is JSON.
        @param column_type: The data type of the column.
        """

        self._table_name = table_name
        self._column_name = to_sql_column_name(column_name, platform)
        self._datasources = list(map(lambda source: MbDataSource(**source), datasources))
        self._nested_json_name = nested_json_name
        self._column_type = column_type

    def get_field(self, pid: int = 0, table_tracker: dict = None) -> Dict[str, Union[str, None]]:
        """
        Generates a random field for the column based on the given data sources and probabilities.

        @param pid: Process ID. This is required for the case when multiple processes are generating fields
                    concurrently. The Process ID ensures each process is able to track its own field
                    generation count independently, avoiding potential race conditions between processes.
        @param table_tracker: A dictionary for keeping track of dataclass counts.
        @return: A dictionary containing the column name and the generated field value.
        """

        # get the names and probabilities as separate lists
        probabilities = list(dc_source.datasource_ratio for dc_source in self._datasources)
        random_dc_source = random.choices(self._datasources, probabilities)[0]

        target_data = random_dc_source.get_target_data()

        if self._column_type == "json":
            target_data = json.dumps({self._nested_json_name: target_data})

        if table_tracker is not None:
            MockingbirdDBTableTracker.increment_column_dataclass(table_name=self._table_name,
                                                                 table_tracker=table_tracker,
                                                                 column_name=self._column_name,
                                                                 dataclass_name=random_dc_source.datasource_name,
                                                                 pid=pid)
        return {self._column_name: target_data}

    @property
    def column_name(self):
        return self._column_name

    @property
    def column_type(self):
        return self._column_type
