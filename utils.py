import ast
import json

def is_stringified_object(val):
    """
    Check if a string value is a stringified list, tuple, or dict.
    """
    if not isinstance(val, str):
        return False
    try:
        parsed = ast.literal_eval(val)
        if isinstance(parsed, (list, tuple, dict)):
            return True
    except:
        pass
    try:
        parsed = json.loads(val)
        if isinstance(parsed, (list, dict)):
            return True
    except:
        pass
    return False

def suggest_transformations(profiling):
    """
    Generate smart suggestions based on profiling info.
    Returns a list of suggestion strings.
    """
    suggestions = []
    for col, info in profiling.items():
        if info['stringified_objects']:
            suggestions.append(f"Flatten Column {col} — detected JSON or stringified object")
        if info['null_heavy']:
            suggestions.append(f"Drop Column {col} — {info['null_ratio']*100:.1f}% nulls")
        if info['mixed_types']:
            suggestions.append(f"Check Column {col} — mixed data types detected")
    return suggestions
