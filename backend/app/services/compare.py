"""Multi-file comparison analysis using AI."""

import json
import os
from openai import OpenAI

from app.core.config import settings
from app.services.file_parser import extract_text, extract_dataframe, SUPPORTED_EXTENSIONS
from app.models.schemas import CompareResponse
from app.utils.serialization import cleanup_serializable

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def find_file_path(file_id: str) -> str:
    for ext in SUPPORTED_EXTENSIONS:
        path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"File not found: {file_id}")


def compare_files(file_ids: list[str], custom_prompt: str | None = None) -> CompareResponse:
    file_texts = {}
    file_stats = {}
    
    for fid in file_ids:
        path = find_file_path(fid)
        text = extract_text(path)
        file_texts[fid] = text[:4000]
        
        # Extract quantitative data
        df = extract_dataframe(path)
        if df is not None:
            numeric_df = df.select_dtypes(include="number")
            file_stats[fid] = numeric_df.mean().to_dict()

    # Calculate Deltas between first two files
    metrics_delta = {}
    if len(file_ids) >= 2:
        f1, f2 = file_ids[0], file_ids[1]
        s1, s2 = file_stats.get(f1, {}), file_stats.get(f2, {})
        
        all_keys = set(s1.keys()) | set(s2.keys())
        for key in all_keys:
            v1 = s1.get(key)
            v2 = s2.get(key)
            if v1 is not None and v2 is not None and v1 != 0:
                delta_pct = ((v2 - v1) / v1) * 100
                metrics_delta[key] = round(delta_pct, 2)

    docs_section = ""
    for fid, text in file_texts.items():
        stats = file_stats.get(fid, {})
        docs_section += f"\n--- Document {fid[:8]} ---\nStats: {stats}\nText: {text}\n"

    user_instruction = ""
    if custom_prompt:
        user_instruction = f"\nAdditional instructions: {custom_prompt}\n"

    prompt = f"""Compare the {len(file_ids)} documents quantitatively and qualitatively.
Metrics Deltas (File 1 to File 2): {metrics_delta}
{user_instruction}
{docs_section}

Return JSON:
{{
    "comparison_summary": "Overall comparison with data-driven highlights",
    "similarities": ["similarity1", "similarity2"],
    "differences": ["difference1", "difference2"],
    "comparative_strategy": "Actionable strategy based on the shifts (deltas) detected.",
    "file_summaries": {{"file_id_short": "summary"}}
}}"""

    response = client.chat.completions.create(
        model=settings.ANALYSIS_MODEL,
        messages=[
            {"role": "system", "content": "You are a senior data analyst. Provide comparative intelligence comparing shifts in metrics and business strategies. Return valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    result = json.loads(response.choices[0].message.content)

    return cleanup_serializable(CompareResponse(
        comparison_summary=result.get("comparison_summary", ""),
        similarities=result.get("similarities", []),
        differences=result.get("differences", []),
        metrics_delta=metrics_delta,
        comparative_strategy=result.get("comparative_strategy", ""),
        file_summaries=result.get("file_summaries", {}),
    ))
