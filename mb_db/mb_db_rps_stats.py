import logging
import time
from multiprocessing import Manager
from threading import Thread


class MockingbirdDbRPSStats(Thread):
    """
    A class for tracking the Rows Per Second (RPS) statistics of a Mockingbird database. Inherits from the Thread class
    to run as a separate thread for continuous monitoring.
    """

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    def __init__(self):
        """
        Initializes the MockingbirdDbRPSStats object and sets up a shared memory manager for rows_written.
        """
        super().__init__()
        self._alive = False

        manager = Manager()
        self._rows_written = manager.Value('i', 0)

    def get_rows_written(self):
        """
        Returns the total number of rows written so far.

        @return: Integer representing the number of rows written.
        """

        return self._rows_written

    def __enter__(self):
        """
        Starts the RPS monitoring thread when entering a context.

        @return: Self.
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Kills the RPS monitoring thread when exiting a context.
        """
        self.kill()

    def run(self):
        """
        Main loop for RPS monitoring. Continuously calculates and prints the RPS average every 3 seconds.
        """
        self._alive = True
        while self._alive:
            rows_written = self._rows_written.value
            time.sleep(3)
            rows_written_last_3s = self._rows_written.value - rows_written
            MockingbirdDbRPSStats.logger.info("Average rows written in the last 3 seconds: {:.2f} row(s)/second".format(rows_written_last_3s / 3))

    def kill(self):
        """
        Stops the RPS monitoring loop.
        """
        self._alive = False
