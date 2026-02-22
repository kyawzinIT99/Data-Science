import math
import numpy as np

def cleanup_serializable(obj):
    """Recursively replace NaN and Inf with safe values for JSON serialization."""
    # Handle Pydantic models
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    elif hasattr(obj, "dict"):
        obj = obj.dict()

    if isinstance(obj, dict):
        return {k: cleanup_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [cleanup_serializable(x) for x in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    elif isinstance(obj, (np.float32, np.float64)):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    return obj
