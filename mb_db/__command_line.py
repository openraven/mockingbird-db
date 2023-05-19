import os
import shutil
from argparse import ArgumentParser
from pathlib import Path

import pkg_resources

from mb_db import MockingbirdDB
from mb_db.mb_db_rps_stats import MockingbirdDbRPSStats


def entry():
    parser = ArgumentParser()
    parser.add_argument("-c", "--config-path", default=None,
                        help="Specifies the path to the user's config file for a mockingbird-db session."
                             " A sample config file can be generated using the '--workspace' argument.")
    parser.add_argument("-p", "--processes", type=int, default=1,
                        help="Specifies the number of processes to use in parallel when 'flooding' a db with rows."
                             " This determines the number of resources the script will use, and affects the performance of the script."
                             " If not provided, the program will run single-processed.")
    parser.add_argument("-w", "--workspace", default=None,
                        help="Creates a new workspace in the designated workspace directory."
                             " This represents the folder to be created on disk."
                             " It creates a boilerplate workspace with an example config file and a small dataset containing 10 SSNs, enough to get started using the example config file.")
    parser.add_argument("-m", "--metadata-path", default=None,
                        help="Specifies the output file path where the metadata should be written.")
    args = parser.parse_args()

    config_path = args.config_path
    processes = args.processes
    workspace = args.workspace
    metadata_path = args.metadata_path

    if workspace:
        create_workspace(args.workspace)
        return

    if args.config_path:
        with MockingbirdDbRPSStats() as mb_stats:
            table = MockingbirdDB(config_path=Path(config_path),
                                  rows_written=mb_stats.get_rows_written())
            table.process(processes)
            if metadata_path:
                table.dump_metadata(Path(metadata_path))


def create_workspace(directory_path):
    directory_path = Path(os.path.abspath(directory_path))
    if os.path.exists(directory_path):
        raise Exception(f"{directory_path} already exists")
    os.mkdir(directory_path)

    example_config = pkg_resources.resource_filename(__name__, "example_config.yaml")
    shutil.copy(example_config, directory_path)

    datasets_path = directory_path / "datasets"
    os.mkdir(datasets_path)

    ssn_list = ['793-76-4095', '246 07 3347', '327-60-7237', '867-11-8206', '578-34-1185', '783-58-3588', '828-67-9021', '212-30-9058', '708-65-3309', '158 02 2866']
    with open(datasets_path / "us_ssn.csv", "w+") as f:
        f.write("ssn\n")

        for ssn in ssn_list:
            f.write(f"{ssn}\n")