import hashlib
import random
from pathlib import Path
from typing import Union, List


class MbDataSource:
    """
    A class representing a data source for a Mockingbird database column, responsible for loading and providing random data.
    """
    def __init__(self,
                 datasource_name: str,
                 datasource_path: str,
                 datasource_ratio: float):
        """
        Initializes the MbDataSource object with the given parameters.

        @param datasource_name: The name of the data source.
        @param datasource_path: The path to the data source file or a special keyword (null or random_data).
        @param datasource_ratio: The probability of this data source being selected.
        """
        self._datasource_name = datasource_name
        self._datasource_path = datasource_path
        self._datasource_ratio = datasource_ratio

        if datasource_path in ['null', 'random_data']:
            self._dataset = []
        else:
            self._dataset = self._load_dataset(Path(self._datasource_path))

    def get_target_data(self) -> Union[str, None]:
        """
        Generates and returns a random data entry from the data source.

        @return: A random data entry if the data source has a path to a dataset, None if the path is 'null', or
                 a random hash if the path is 'random_data'.
        """
        if self._datasource_path == "null":
            return None
        if self._datasource_path == "random_data":
            return hashlib.sha256(str(random.getrandbits(256)).encode('utf-8')).hexdigest()
        return random.choice(self._dataset)

    @staticmethod
    def _load_dataset(dataset_folder: Path) -> List[str]:
        """
        Loads a dataset from the given dataset folder.

        @param dataset_folder: A pathlib.Path object representing the dataset folder.
        @return: A list of strings, each representing a line in the dataset.
        """
        with open(dataset_folder) as f:
            lines = f.read().split('\n')
        lines.pop(0)  # remove the csv header

        return lines

    @property
    def datasource_name(self):
        return self._datasource_name

    @property
    def datasource_ratio(self):
        return self._datasource_ratio
