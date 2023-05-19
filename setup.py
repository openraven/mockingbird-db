from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="mockingbird-db",
    version="1.0",
    packages=find_packages(),
    package_data={'': ['example_config.yaml']},
    install_requires=[
        "numpy==1.24.2",
        "psycopg2-binary==2.9.5",
        "PyYAML==6.0",
        "pyodbc==4.0.35",
        "mysql-connector-python==8.0.32",
        "PyMySQL==1.0.3",
    ],
    entry_points={
        "console_scripts": [
            "mockingbird-db=mb_db.__command_line:entry",
        ],
    },
    url='https://github.com/openraven/mockingbird-db',
    include_package_data=True,
    description="Mockingbird-DB: Populate databases with synthetic data",
    long_description=long_description,
    long_description_content_type="text/markdown",
)

