import modal
import os

# Define the Modal App
app = modal.App("ai-data-analysis")

# Define the environment image with all DS dependencies and app code
image = (
    modal.Image.debian_slim()
    .pip_install(
        "pandas",
        "numpy",
        "scikit-learn",
        "hdbscan",
        "prophet",
        "statsmodels",
        "openai",
        "pydantic",
        "networkx",
        "pingouin",
        "openpyxl",
        "aiofiles"
    )
    .env({"PYTHONPATH": "/root"})
    .add_local_dir(
        os.path.join(os.path.dirname(__file__), "app"),
        remote_path="/root/app"
    )
)

# Persistent volume for data storage
volume = modal.Volume.from_name("data-analysis-storage", create_if_missing=True)

@app.function(image=image, volumes={"/data": volume})
def check_file_on_volume(file_id: str, file_ext: str) -> bool:
    """Check if a file exists on the persistent volume."""
    path = f"/data/uploads/{file_id}{file_ext}"
    return os.path.exists(path)

@app.function(image=image, volumes={"/data": volume})
def save_file_to_volume(file_id: str, file_ext: str, content: bytes):
    """Save a file to the persistent volume."""
    os.makedirs("/data/uploads", exist_ok=True)
    path = f"/data/uploads/{file_id}{file_ext}"
    with open(path, "wb") as f:
        f.write(content)
    volume.commit()
    return True

@app.function(image=image, volumes={"/data": volume}, timeout=600)
def run_forecast(file_id: str, file_ext: str, date_col: str, value_col: str, file_content: bytes = None):
    """Run time-series forecasting on Modal, using Volume if file_id exists."""
    import pandas as pd
    import io
    from app.services.forecast import PriceForecaster
    
    vol_path = f"/data/uploads/{file_id}{file_ext}"
    temp_path = f"/tmp/{file_id}{file_ext}"
    
    if os.path.exists(vol_path):
        data_path = vol_path
    elif file_content:
        # Fallback to provided content if not on volume
        with open(temp_path, "wb") as f:
            f.write(file_content)
        data_path = temp_path
    else:
        raise ValueError(f"File /data/uploads/{file_id}{file_ext} not found on volume and no content provided")
        
    forecaster = PriceForecaster(data_path, date_column=date_col, price_column=value_col)
    forecaster.load_data()
    metrics = forecaster.train_model()
    forecast = forecaster.predict_next_months(3)
    decomposition = forecaster.decompose_series()
    
    return {
        "metrics": metrics,
        "forecast": forecast.to_dict(orient="records") if not forecast.empty else [],
        "decomposition": decomposition
    }

@app.function(image=image, volumes={"/data": volume}, timeout=600)
def run_segmentation(df_json: str = None, file_id: str = None, file_ext: str = None):
    """Run HDBSCAN clustering on Modal using JSON or file from Volume."""
    import pandas as pd
    import io
    import json
    from app.services.analyzer import classify_segments
    
    if file_id and file_ext:
        path = f"/data/uploads/{file_id}{file_ext}"
        if os.path.exists(path):
            if file_ext == ".csv":
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
        else:
             df = pd.read_json(io.StringIO(df_json))
    else:
        df = pd.read_json(io.StringIO(df_json))
        
    segments = classify_segments(df)
    
    # Convert segments to dict for serialization
    return [s.model_dump() if hasattr(s, 'model_dump') else s.dict() for s in segments]

@app.function(
    image=image, 
    volumes={"/data": volume}, 
    secrets=[modal.Secret.from_name("openai-api-key")],
    timeout=300
)
def run_agent_analysis(role: str, focus: str, prompt_data: str):
    """Run a single LLM agent analysis on Modal."""
    from openai import OpenAI
    import os
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in Modal secrets")
        
    client = OpenAI(api_key=api_key)
    sys_prompt = f"You are the {role}. {focus}"
    user_prompt = f"Based on the following data, provide your analysis and recommendations:\n{prompt_data}"
    
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content

@app.function(image=image, volumes={"/data": volume}, timeout=600)
def run_data_merge(file_ids: list[str], file_exts: list[str]):
    """Merge multiple files from the Volume on Modal."""
    import pandas as pd
    import os
    import uuid
    
    dfs = []
    for f_id, f_ext in zip(file_ids, file_exts):
        path = f"/data/{f_id}{f_ext}"
        if not os.path.exists(path):
            continue
            
        if f_ext == ".csv":
            try:
                df = pd.read_csv(path)
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding='latin1')
        else:
            df = pd.read_excel(path)
        dfs.append(df)
        
    if not dfs:
        return {"error": "No files found on volume"}
        
    # Standard merge logic
    common_cols = list(set.intersection(*[set(df.columns) for df in dfs]))
    if common_cols and len(common_cols) > 0:
        merged_df = dfs[0]
        for df in dfs[1:]:
            merged_df = pd.merge(merged_df, df, on=common_cols[0], how='outer', suffixes=('', '_dup'))
    else:
        merged_df = pd.concat(dfs, axis=1)
        
    merged_df = merged_df.loc[:,~merged_df.columns.duplicated()]
    
    merged_id = f"merged_{uuid.uuid4().hex[:8]}"
    merged_path = f"/data/uploads/{merged_id}.csv"
    os.makedirs("/data/uploads", exist_ok=True)
    merged_df.to_csv(merged_path, index=False)
    volume.commit()
    
    return {
        "file_id": merged_id,
        "filename": f"merged_dataset_{len(file_ids)}.csv",
        "file_size": os.path.getsize(merged_path)
    }

@app.function(image=image, volumes={"/data": volume}, timeout=300)
def run_data_audit(file_id: str, file_ext: str):
    """Run heavy anomaly detection and quality audit on Modal."""
    import pandas as pd
    import os
    from app.services.analyzer import detect_anomalies, calculate_data_quality
    
    path = f"/data/uploads/{file_id}{file_ext}"
    if not os.path.exists(path):
        return {"error": "File not found"}
        
    if file_ext == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
        
    anomalies = detect_anomalies(df)
    quality = calculate_data_quality(df)
    
    # Convert Pydantic models to dict
    return {
        "anomalies": [a.model_dump() if hasattr(a, 'model_dump') else a.dict() for a in anomalies],
        "quality": quality.model_dump() if hasattr(quality, 'model_dump') else quality.dict()
    }
