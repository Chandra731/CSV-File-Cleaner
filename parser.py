import pandas as pd
import io
import zipfile
import requests
import ast
import json

def load_file(file, from_url=False):
    """
    Load file from uploaded file or URL and return a pandas DataFrame.
    Supports CSV, TXT, XLSX, JSON, TSV, ZIP (containing CSV).
    """
    if from_url:
        response = requests.get(file)
        content = response.content
        filename = file.split("/")[-1]
        file_obj = io.BytesIO(content)
    else:
        file_obj = file
        filename = file.name

    if filename.endswith('.zip'):
        with zipfile.ZipFile(file_obj) as z:
            # Find first CSV file in zip
            for f in z.namelist():
                if f.endswith('.csv'):
                    with z.open(f) as csvfile:
                        return pd.read_csv(csvfile)
            raise ValueError("No CSV file found in the ZIP archive.")
    elif filename.endswith('.csv') or filename.endswith('.txt') or filename.endswith('.tsv'):
        sep = ',' if filename.endswith('.csv') or filename.endswith('.txt') else '\t'
        return pd.read_csv(file_obj, sep=sep)
    elif filename.endswith('.xlsx'):
        return pd.read_excel(file_obj)
    elif filename.endswith('.json'):
        # For JSON, try to load and flatten if nested
        df = pd.read_json(file_obj)
        if any(isinstance(i, dict) for i in df.iloc[0]):
            df = flatten_nested_json(df)
        return df
    else:
        raise ValueError("Unsupported file type: " + filename)

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

def flatten_nested_json(df):
    """
    Recursively flatten nested JSON/dictionaries in a DataFrame.
    """
    from pandas import json_normalize
    while True:
        # Find columns with dict or list
        dict_cols = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, dict)).any()]
        list_cols = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, list)).any()]
        if not dict_cols and not list_cols:
            break
        for col in dict_cols:
            normalized = json_normalize(df[col])
            normalized.columns = [f"{col}.{subcol}" for subcol in normalized.columns]
            df = df.drop(columns=[col]).join(normalized)
        for col in list_cols:
            # Explode lists into multiple rows
            df = df.explode(col).reset_index(drop=True)
    return df
