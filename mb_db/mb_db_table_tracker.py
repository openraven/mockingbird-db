from collections import defaultdict
from multiprocessing import Manager
from typing import Dict, Union, Any

TableContentsType = Dict[str, Dict[str, int]]
TableTrackerType = Dict[str, Union[str, TableContentsType]]


class MockingbirdDBTableTracker:
    """
    A class for keeping track of the dataclasses in a Mockingbird database table.
    """

    @staticmethod
    def key_formatter(table_name: str, column_name: str, dataclass_name: str, pid: int) -> str:
        # Formats the key by joining table name, column name, dataclass name, and pid with a semicolon.
        # The pid (Process ID) is necessary as each process will increment the count independently.
        # Including the pid in the key ensures that each process writes to its unique key, thus avoiding
        # any potential race conditions between the processes.
        return f"{table_name};{column_name};{dataclass_name};{pid}"

    @staticmethod
    def increment_column_dataclass(table_tracker: Dict[str, int],
                                   table_name: str,
                                   column_name: str,
                                   dataclass_name: str,
                                   pid: int):
        # Increments the count of the dataclass in the given table and column.
        key = MockingbirdDBTableTracker.key_formatter(table_name, column_name, dataclass_name, pid)
        if key not in table_tracker:
            table_tracker[key] = 0

        table_tracker[key] += 1  # Increment the count.


class MockingbirdDBTableTrackerWriter:
    """
    A class for processing a set of MockingbirdDBTableTracker objects and generating metadata in a readable format.
    """

    def __init__(self, mb_db_tables_trackers: Dict[str, int]):
        self._mb_db_tables_trackers = mb_db_tables_trackers

    def create_metadata(self) -> Dict[str, Any]:
        metadata = {}
        tables = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        # Iterate over all the keys and counts in the table tracker.
        for key, count in self._mb_db_tables_trackers.items():
            table_name, column_name, dataclass_name, pid = key.split(';')

            # As the Manager's dict cannot handle nested dicts directly, we're "flattening" the dictionary structure
            # using semicolons to concatenate the keys. Here we split the key again to extract the original values
            # and use them to populate the nested dictionaries in memory (outside of the Manager's dict).
            tables[table_name][column_name][dataclass_name] += count

        # Convert the data back into a nested dict format for easier reading and understanding.
        metadata['tables'] = []
        for table_name, columns in tables.items():
            table_metadata = {"table_name": table_name, "contents": []}
            for column_name, dataclasses in columns.items():
                for dataclass_name, count in dataclasses.items():
                    table_metadata["contents"].append({
                        "column_name": column_name,
                        "dataclass_name": dataclass_name,
                        "dataclass_count": count
                    })
            metadata['tables'].append(table_metadata)

        return metadata


from multiprocessing import Process


def worker(mb_db, table_name, column_name, dataclass_name, pid):
    for _ in range(1000):  # this number can be adjusted according to your needs
        MockingbirdDBTableTracker.increment_column_dataclass(mb_db, table_name, column_name, dataclass_name, pid)


if __name__ == "__main__":
    import pprint

    manager = Manager()
    mb_db = manager.dict()

    processes = []
    for pid in range(10):  # this number can be adjusted according to your needs
        p = Process(target=worker, args=(mb_db, "mb1", "us_ssn", "US Social Security Number", pid))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    mb_tb_trker_wrtr = MockingbirdDBTableTrackerWriter(mb_db)
    pprint.pprint(mb_tb_trker_wrtr.create_metadata())
