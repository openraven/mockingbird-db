import re


def to_sql_column_name(column_name, platform):
    if platform == "mysql":
        enclose_character = "`"
    else:
        enclose_character = '"'

    # Replace non-alphanumeric characters with underscores
    column_name = re.sub(r'[^a-zA-Z0-9_]', '_', column_name)
    # Remove leading and trailing underscores
    column_name = column_name.strip('_')
    column_name = column_name.lower()
    column_name = f"{enclose_character}{column_name}{enclose_character}"
    return column_name
