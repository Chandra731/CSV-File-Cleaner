import pandas as pd
import ast
import json

def detect_column_types(df):
    """
    Detect column-wise type distribution and flag mixed types, stringified objects, and null-heavy columns.
    Returns a dict with column names as keys and profiling info as values.
    """
    profiling = {}
    for col in df.columns:
        col_data = df[col]
        type_counts = {}
        mixed_flag = False
        stringified_obj_flag = False
        null_count = col_data.isnull().sum()
        total_count = len(col_data)
        null_ratio = null_count / total_count if total_count > 0 else 0

        for val in col_data.dropna():
            val_type = type(val).__name__
            type_counts[val_type] = type_counts.get(val_type, 0) + 1

            # Check for stringified objects
            if val_type == 'str':
                try:
                    parsed = ast.literal_eval(val)
                    if isinstance(parsed, (list, tuple, dict)):
                        stringified_obj_flag = True
                except:
                    pass

        if len(type_counts) > 1:
            mixed_flag = True

        profiling[col] = {
            'type_distribution': {k: v / total_count for k, v in type_counts.items()},
            'mixed_types': mixed_flag,
            'stringified_objects': stringified_obj_flag,
            'null_ratio': null_ratio,
            'null_heavy': null_ratio > 0.5
        }
    return profiling

def parse_stringified(val):
    """
    Parse stringified list, tuple, or dict using ast.literal_eval or json.loads.
    """
    if not isinstance(val, str):
        return val
    try:
        return ast.literal_eval(val)
    except:
        try:
            return json.loads(val)
        except:
            return val

def flatten_dict(d, parent_key='', sep='.'):
    """
    Recursively flatten nested dictionaries.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def parse_and_flatten_column(df, col):
    """
    Parse stringified objects in a column and flatten dictionaries into multiple columns.
    """
    parsed_col = df[col].apply(parse_stringified)
    # Check if parsed_col contains dicts
    if parsed_col.apply(lambda x: isinstance(x, dict)).any():
        # Flatten dicts into separate columns
        flattened = parsed_col.apply(lambda x: flatten_dict(x) if isinstance(x, dict) else {})
        flattened_df = pd.json_normalize(flattened)
        # Prefix new columns with original column name
        flattened_df.columns = [f"{col}.{subcol}" for subcol in flattened_df.columns]
        df = df.drop(columns=[col]).join(flattened_df)
    else:
        df[col] = parsed_col
    return df

def explode_list_column(df, col):
    """
    Explode list or tuple column into multiple rows.
    """
    if df[col].apply(lambda x: isinstance(x, (list, tuple))).any():
        df = df.explode(col).reset_index(drop=True)
    return df
