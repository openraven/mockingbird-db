# Mockingbird-DB

Mockingbird-DB is a powerful and flexible Python tool designed to populate databases with synthetic data, based on user-defined configurations. It supports a variety of popular database platforms, such as PostgreSQL, MSSQL, and MySQL, and allows users to customize their data generation process through an intuitive YAML configuration file format. By defining table structures, column types, and data sources with different ratios, users can create a wide range of realistic, yet synthetic data scenarios tailored to their specific needs.

Featuring both single-process and multi-process workloads, Mockingbird-DB can effortlessly scale to accommodate databases of varying sizes and complexities. The tool also provides insightful metadata output, enabling users to analyze the distribution of data sources and the overall structure of the populated tables.

## Installation

To install Mockingbird-DB, simply clone the repository and install:

```bash
git clone https://github.com/openraven/mockingbird-db.git
cd mockingbird-db
pip3 install .
```

or more simply using pypi by running

```bash
pip3 install mockingbird-db
```

## Getting Started

### Create a Workspace

To create a new workspace with an example configuration file and a small dataset containing 10 SSNs, run the following command:

```bash
mockingbird-db --workspace /path/to/your/workspace
```

This will create a new directory at the specified path, containing a boilerplate workspace with an example configuration file and a small dataset.


### Edit the Configuration File

Once you have the configuration file, you can customize it to define the synthetic data generation process according to your requirements. The main components that can be edited in the configuration file are:

1. **Database Information (`db_info`)**: This section allows you to set up the connection to your database. You can define:
    - `connection_type`: Choose between "arguments" or "url" to specify how to connect to the database.
    - `platform`: Specify the database platform, such as "postgres", "mssql", or "mysql".
    - `url`: If using the "url" connection type, provide the full connection URL.
    - `arguments`: If using the "arguments" connection type, provide the required connection arguments such as host, port, user, password, and database name.

2. **Tables (`tables`)**: Define one or more tables to be populated with synthetic data. For each table, you can customize the following properties:
    - `table_name`: The name of the table to be created or populated.
    - `rows`: The number of rows to insert into the table.
    - `columns`: Define the columns in the table and their respective properties:
        - `column_name`: The name of the column.
        - `datasources`: A list of data sources to use for using your synthetic data sources. 
            - `datasource_name`: The name of the data source.
            - `datasource_path`: The path to the dataset file, "random_data" for generating random data, or "null" for null data.
            - `datasource_ratio`: The probability of using this data source for generating the column's data.
        - `nested_json_name`: The name of the nested JSON field, if applicable.
        - `column_type`: The data type of the column (e.g., "string", "json").

Feel free to adjust the configuration file according to your specific use case, specifying the desired database connection information, table structure, and synthetic data sources.
### Run Mockingbird-DB

To start populating your database tables with synthetic data, run the following command:

```bash
mockingbird-db --config-path /path/to/your/workspace/config.yaml
```

Optionally, you can specify the number of processes to use in parallel when flooding the database with rows by adding the `-p` or `--processes` flag:

```bash
mockingbird-db --config-path /path/to/your/workspace/config.yaml --processes 4
```

### Save Metadata

To save the metadata of the populated tables to a file, specify the `-m` or `--metadata-path` flag followed by the output file path:

```bash
mockingbird-db --config-path /path/to/your/workspace/config.yaml --metadata-path /path/to/your/output/metadata.json
```

This will generate a JSON file containing metadata information about the populated tables, such as the number of rows and the distribution of data sources for each column.

## Contributing

Contributions to Mockingbird-DB are welcome! Feel free to open an issue or submit a pull request on GitHub to improve the project or to add new features.