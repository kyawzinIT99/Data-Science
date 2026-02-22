import json
from openai import OpenAI
import pandas as pd
import numpy as np
import io

import logging
import os

# Fix for KMeans crash on Mac
os.environ["OMP_NUM_THREADS"] = "1"

# Setup explicit file logging
# Setup explicit file logging
LOG_FILE = '/tmp/backend_error.log'
logger = logging.getLogger(__name__)
if not logger.handlers:
    # File handler
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    logger.setLevel(logging.INFO)

from app.core.config import settings
from app.models.schemas import (
    AnalysisResponse, ChartSuggestion, DashboardResponse,
    ProfitLossData, GrowthSuggestion, CorrelationMetric, AnomalyAlert,
    DataQualityReport, FeatureImportanceMetric, DataSegment, AgentInsight
)
import math
from app.utils.serialization import cleanup_serializable

def safe_float(val, default=0.0):
    """Ensure a value is a valid JSON-serializable float (not NaN or Inf)."""
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default

from sklearn.ensemble import RandomForestRegressor
import hdbscan
from sklearn.preprocessing import StandardScaler, LabelEncoder
from app.services.language import detect_language, get_analysis_system_prompt
from app.services.forecast import PriceForecaster
from app.utils.modal import get_modal_func


def _get_client(api_key: str | None = None) -> OpenAI:
    return OpenAI(api_key=api_key or settings.OPENAI_API_KEY)


client = _get_client()


def refine_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and refine dataframe for statistical/ML analysis."""
    df = df.copy()
    
    # 1. Handle Infinity and NaNs in numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Replace Inf with NaN
        df[col] = df[col].replace([np.inf, -np.inf], np.nan)
        # Ensure numeric type
        df[col] = pd.to_numeric(df[col], errors='coerce')
        # Fill NaNs with 0 to prevent crash downstream
        df[col] = df[col].fillna(0.0)

    # 2. Try to fix numeric columns labeled as object
    for col in df.select_dtypes(include=['object']).columns:
        # If > 50% looks numeric, force it
        sample = df[col].dropna().head(100)
        if len(sample) > 0:
            # 2a. Date extraction: if it's named 'date', 'time', or 'timestamp'
            col_lower = col.lower()
            if 'date' in col_lower or 'time' in col_lower or 'stamp' in col_lower or 'day' in col_lower or 'month' in col_lower or 'year' in col_lower:
                try:
                    # Parse with format mixed and dayfirst to catch European dates (25-02-2022)
                    parsed_dates = pd.to_datetime(df[col], errors='coerce', format='mixed', dayfirst=True)
                    
                    # Also try a straight parse for non-standard formats that mixed struggles with
                    if parsed_dates.isna().sum() > len(df) * 0.7:
                        parsed_dates = pd.to_datetime(df[col], errors='coerce')

                    # Clean up: only fill if we have some data
                    if parsed_dates.notna().any():
                        parsed_dates = parsed_dates.ffill().bfill() 
                        df[col] = parsed_dates
                    
                    # Store as original datetime for now, let JSON serialier handle the final conversion
                    df[col] = df[col].dt.strftime('%Y-%m-%d')
                    continue
                except Exception as e:
                    pass

            # 2b. Numeric extraction
            try:
                # Clean strings: remove currency symbols, commas, and strip whitespace
                clean_sample = sample.astype(str).str.replace(r'[$,%]', '', regex=True).str.strip()
                # If it's a numeric string that got interpreted as object
                numeric_sample = pd.to_numeric(clean_sample, errors='coerce')
                if numeric_sample.notna().sum() / len(sample) > 0.5:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[$,%]', '', regex=True).str.strip(), errors='coerce').fillna(0.0)
            except Exception:
                pass
                
    # Final sweep to catch any Infs created during string->numeric conversion
    numeric_cols_final = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols_final:
        df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        
    return df


def analyze_document(file_id: str, text: str, df: pd.DataFrame | None = None, custom_prompt: str | None = None, api_key: str | None = None, language: str | None = None) -> AnalysisResponse:
    if df is not None:
        df = refine_dataframe(df)

    data_context = ""
    if df is not None:
        data_context = f"""
Data Statistics:
- Rows: {len(df)}, Columns: {len(df.columns)}
- Column names: {', '.join(df.columns.tolist())}
- Data types: {df.dtypes.to_string()}
- Numeric summary: {df.describe().to_string()}
"""

    custom_instruction = ""
    if custom_prompt:
        custom_instruction = f"\nSpecial focus requested by user: {custom_prompt}\n"

    prompt = f"""Analyze the following document content and provide a structured analysis.
{custom_instruction}
{data_context}

Document content (first 8000 chars):
{text[:8000]}

Respond in this exact JSON format:
{{
    "summary": "A comprehensive 3-5 sentence summary",
    "key_insights": ["insight1", "insight2", "insight3"],
    "trends": ["trend1", "trend2"],
    "recommendations": ["recommendation1", "recommendation2"]
}}"""

    lang_code = language
    if not lang_code:
        lang_code, _ = detect_language(text)
    
    system_prompt = get_analysis_system_prompt(lang_code)
    ai_client = _get_client(api_key) if api_key else client

    response = ai_client.chat.completions.create(
        model=settings.ANALYSIS_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    try:
        result = json.loads(response.choices[0].message.content)
    except Exception:
        result = {"summary": "Analysis unavailable", "key_insights": [], "trends": [], "recommendations": []}

    data_stats = None
    if df is not None:
        data_stats = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "missing_values": df.isnull().sum().to_dict(),
        }

    return AnalysisResponse(
        file_id=file_id,
        summary=result.get("summary", ""),
        key_insights=result.get("key_insights", []),
        trends=result.get("trends", []),
        recommendations=result.get("recommendations", []),
        data_stats=data_stats,
    )


def calculate_correlations(df: pd.DataFrame) -> list[CorrelationMetric]:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return []

    corr_matrix = numeric_df.corr()
    metrics = []

    # Get top correlations, avoiding self-correlation and duplicates
    columns = corr_matrix.columns
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            col_a = columns[i]
            col_b = columns[j]
            raw_val = corr_matrix.iloc[i, j]
            val = safe_float(raw_val, default=0.0)

            # Skip NaN/zero correlations
            if val == 0.0 and (pd.isna(raw_val) or raw_val == 0):
                continue

            if abs(val) > 0.5: # Only significant correlations
                desc = f"Strong positive relationship" if val > 0.7 else "Moderate positive relationship"
                if val < -0.7: desc = "Strong negative relationship"
                elif val < -0.5: desc = "Moderate negative relationship"

                metrics.append(CorrelationMetric(
                    column_a=str(col_a),
                    column_b=str(col_b),
                    correlation=round(val, 4),
                    description=desc
                ))

    # Sort by absolute strength
    metrics.sort(key=lambda x: abs(x.correlation), reverse=True)
    return metrics[:5] # Return top 5 drivers


def detect_anomalies(df: pd.DataFrame) -> list[AnomalyAlert]:
    numeric_df = df.select_dtypes(include=[np.number])
    alerts = []

    for col in numeric_df.columns:
        series = numeric_df[col].dropna()
        if len(series) < 5: continue

        mean = series.mean()
        std = series.std()

        if std == 0: continue

        # Calculate Z-scores
        z_scores = (series - mean) / std
        anomalies = series[abs(z_scores) > 2.5] # 2.5 standard deviations for outliers

        for idx, val in anomalies.items():
            try:
                # Use the integer position if the index label is not an int
                row_idx = int(idx) if isinstance(idx, (int, np.integer)) else -1
                
                z = z_scores[idx]
                severity = "High" if abs(z) > 3.5 else "Moderate"
                alerts.append(AnomalyAlert(
                    column=str(col),
                    row_index=row_idx,
                    value=safe_float(val),
                    reason=f"{severity} outlier detected ({round(safe_float(z), 1)} standard deviations from mean)"
                ))
            except Exception:
                continue
            if len(alerts) >= 10: break # Cap alerts

    return alerts[:10]

def calculate_data_quality(df: pd.DataFrame) -> DataQualityReport:
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0

    duplicates = df.duplicated().sum()
    duplicate_pct = (duplicates / len(df) * 100) if len(df) > 0 else 0

    # Simple variance health (check if numeric columns have 0 variance)
    numeric_df = df.select_dtypes(include=[np.number])
    zero_variance_cols = [col for col in numeric_df.columns if numeric_df[col].std() == 0]

    # Scoring logic: Start at 100, deduct for missing data and duplicates
    score = 100 - (missing_pct * 0.5) - (duplicate_pct * 0.3)
    if len(numeric_df.columns) > 0:
        score -= (len(zero_variance_cols) / len(numeric_df.columns) * 10)

    score = max(0, min(100, score))

    issues = []
    if missing_pct > 5: issues.append(f"High missing data rate ({round(missing_pct, 1)}%)")
    if duplicate_pct > 2: issues.append(f"Detected {duplicates} duplicate rows")
    if zero_variance_cols: issues.append(f"Zero variance in column: {zero_variance_cols[0]}")

    try:
        var_score = safe_float(numeric_df.var().mean(), default=0.0)
    except Exception:
        var_score = 0.0

    return DataQualityReport(
        score=round(score, 1),
        missing_values_count=int(missing_cells),
        duplicates_count=int(duplicates),
        variance_score=round(safe_float(var_score), 2),
        issues=issues
    )

def calculate_feature_importance(df: pd.DataFrame) -> list[FeatureImportanceMetric]:
    # Ensure dataframe is refined
    df = refine_dataframe(df)
    
    numeric_df = df.select_dtypes(include=[np.number]).copy()
    # Drop columns that are entirely NaN/Inf after refinement
    numeric_df = numeric_df.dropna(axis=1, how='all')
    
    if numeric_df.shape[1] < 2: return []

    # Identify target (prefer Revenue/Sales/Price)
    target_col = None
    for col in numeric_df.columns:
        c = col.lower()
        if any(x in c for x in ["revenue", "sales", "price", "profit"]):
            target_col = col
            break

    if not target_col:
        target_col = numeric_df.columns[-1] # Default to last column

    y = numeric_df[target_col].fillna(numeric_df[target_col].mean() if not numeric_df[target_col].isna().all() else 0)
    X = numeric_df.drop(columns=[target_col]).fillna(numeric_df.mean().fillna(0))

    # Final check for Inf/NaN which RandomForest cannot handle
    if not np.isfinite(y).all() or not np.isfinite(X).all().all():
        # Replace remaining Infs with large numbers if any, though refine_dataframe should have caught them
        y = y.replace([np.inf, -np.inf], 0).fillna(0)
        X = X.replace([np.inf, -np.inf], 0).fillna(0)

    if X.empty: return []

    try:
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        importances = model.feature_importances_

        metrics = []
        for i, col in enumerate(X.columns):
            score = float(importances[i])
            impact = "High" if score > 0.4 else "Medium" if score > 0.1 else "Low"
            
            # Simple direction via correlation
            correlation = X[col].corr(y)
            contribution = "Positive" if correlation > 0.1 else "Negative" if correlation < -0.1 else "Neutral"
            
            metrics.append(FeatureImportanceMetric(
                feature_name=col,
                importance_score=round(safe_float(score), 3),
                impact_level=impact,
                contribution_type=contribution
            ))

        metrics.sort(key=lambda x: x.importance_score, reverse=True)
        return metrics[:5]
    except Exception:
        return []

def classify_segments(df: pd.DataFrame, file_id: str = None) -> list[DataSegment]:
    # --- Modal Remote Execution Hook ---
    modal_run = get_modal_func("run_segmentation")
    if modal_run:
        try:
            from app.utils.modal import sync_file_to_modal
            file_ext = ".csv"
            # Find actual file path if file_id exists
            from app.services.chat import _find_file_path
            f_path = _find_file_path(file_id) if file_id else None
            
            if f_path and sync_file_to_modal(file_id, f_path):
                logger.info(f"Offloading segmentation to Modal (via Volume: {file_id})...")
                remote_segments = modal_run.remote(file_id=file_id, file_ext=file_ext)
            else:
                logger.info("Offloading segmentation to Modal (via JSON fallback)...")
                remote_segments = modal_run.remote(df_json=df.to_json())
                
            return [DataSegment(**s) for s in remote_segments]
        except Exception as e:
            logger.warning(f"Modal segmentation failed, falling back to local: {e}")

    df = refine_dataframe(df)
    numeric_df = df.select_dtypes(include=[np.number]).dropna(axis=1, how='all')
    if numeric_df.empty or len(df) < 5: return []
    
    # Preprocessing
    data = numeric_df.fillna(numeric_df.mean().fillna(0))
    # Double check for Inf before scaling
    if not np.isfinite(data).all().all():
        data = data.replace([np.inf, -np.inf], 0).fillna(0)

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)
    
    # Dynamic min_cluster_size based on data volume
    # For very small datasets, we need a small min_cluster_size
    min_size = max(2, int(len(df) * 0.1))
    if len(df) < 10: min_size = 2

    # HDBSCAN clustering
    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_size, gen_min_span_tree=True)
    df = df.copy()
    df['cluster'] = clusterer.fit_predict(scaled_data.astype(np.float64))
    
    segments = []
    cluster_summaries = []
    
    unique_clusters = sorted(df['cluster'].unique())
    
    for cluster_id in unique_clusters:
        cluster_data = df[df['cluster'] == cluster_id]
        size = len(cluster_data)
        
        # Get unique traits of this cluster
        traits = []
        if cluster_id == -1:
            traits.append("Outliers or niche cases")
        else:
            for col in numeric_df.columns:
                try:
                    cluster_avg = float(cluster_data[col].mean())
                    total_avg = float(df[col].mean())
                    if np.isnan(cluster_avg) or np.isnan(total_avg) or total_avg == 0: continue
                    
                    if cluster_avg > total_avg * 1.2: traits.append(f"High {col}")
                    elif cluster_avg < total_avg * 0.8: traits.append(f"Low {col}")
                except Exception:
                    continue
            
        cluster_summaries.append({
            "id": int(cluster_id),
            "size": size,
            "traits": ", ".join(traits[:3]) if traits else "General behavior"
        })
        
    # Use LLM to name and strategize segments
    prompt = f"""Based on these data clusters (HDBSCAN), give them professional business names (e.g. VIP Customers, Emerging Market, High-Cost Operations), describe their shared characteristics, and provide a growth strategy for each. Note: Cluster -1 represents outliers or unclassified points.
    
Clusters:
{json.dumps(cluster_summaries, indent=2)}

Return JSON:
{{
    "segments": [
        {{
            "name": "Professional Name",
            "characteristics": "Detailed description",
            "growth_strategy": "Specific action plan"
        }}
    ]
}}"""

    try:
        ai_client = _get_client(settings.OPENAI_API_KEY)
        response = ai_client.chat.completions.create(
            model=settings.ANALYSIS_MODEL,
            messages=[
                {"role": "system", "content": "You are a business strategist specializing in market segmentation. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        segments_json = result.get("segments", [])
        if not isinstance(segments_json, list):
            segments_json = []

        for i, seg in enumerate(segments_json):
            if i < len(cluster_summaries) and isinstance(seg, dict):
                segments.append(DataSegment(
                    name=str(seg.get("name", f"Segment {cluster_summaries[i]['id']}")),
                    size=int(cluster_summaries[i]["size"]),
                    characteristics=str(seg.get("characteristics", "Shared characteristics")),
                    growth_strategy=str(seg.get("growth_strategy", "Growth plan"))
                ))
        return segments
    except Exception as e:
        logger.error(f"Error in classify_segments: {e}")
        # Fallback for all clusters if LLM failed
        final_segments = []
        for i, summary in enumerate(cluster_summaries):
            final_segments.append(DataSegment(
                name=f"Segment {summary['id']}" if summary['id'] != -1 else "Niche Cases",
                size=int(summary["size"]),
                characteristics=str(summary.get("traits", "Average behavior")),
                growth_strategy="Monitor and optimize operations"
            ))
        return final_segments


def generate_dashboard(file_id: str, text: str, df: pd.DataFrame | None = None, language: str | None = None) -> DashboardResponse:
    try:
        if df is not None:
            df = refine_dataframe(df)

        data_info = ""
        summary_stats = {}
        profit_loss = None
        correlations = []
        anomalies = []
        data_quality = None
        feature_importance = []
        segments = []
        time_series_decomp = None
        agent_insights = []
        detection_profile = "Standard Dataset"

        if df is not None:
            # --- Parallel Analytics execution ---
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # 1. Start all long-running tasks
                future_audit = None
                modal_audit_run = get_modal_func("run_data_audit")
                if modal_audit_run:
                    from app.services.chat import _find_file_path
                    from app.utils.modal import sync_file_to_modal
                    f_path = _find_file_path(file_id)
                    if f_path and sync_file_to_modal(file_id, f_path):
                        logger.info("Parallelizing data audit (Modal)...")
                        future_audit = executor.submit(modal_audit_run.remote, file_id, os.path.splitext(f_path)[1].lower())

                logger.info("Parallelizing correlations, feature importance, and segments...")
                future_corr = executor.submit(calculate_correlations, df)
                future_feat = executor.submit(calculate_feature_importance, df)
                future_segments = executor.submit(classify_segments, df, file_id=file_id)
                
                # Forecasting logic: detect columns first
                import re
                date_pattern = re.compile(r"date|time|stamp|day|month|year|period", re.I)
                val_pattern = re.compile(r"price|revenue|sales|total|value|amount|cost|expense|profit|units|qty", re.I)
                
                date_col = next((c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c]) or date_pattern.search(str(c))), None)
                future_forecast = None
                if date_col:
                    value_col = next((c for c in df.columns if c != date_col and pd.api.types.is_numeric_dtype(df[c]) and val_pattern.search(str(c))), None)
                    if not value_col:
                        num_cols = df.select_dtypes(include=[np.number]).columns
                        if not num_cols.empty: 
                            # Avoid picking index-like columns if possible
                            value_col = next((c for c in num_cols if c != date_col and not any(x in str(c).lower() for x in ["id", "index", "key"])), num_cols[0])
                    
                    if value_col:
                        def _run_forecast_wrapper(f_id, d_col, v_col, d_frame):
                            try:
                                m_forecast = get_modal_func("run_forecast")
                                if m_forecast:
                                    from app.services.chat import _find_file_path
                                    from app.utils.modal import sync_file_to_modal
                                    fp = _find_file_path(f_id)
                                    if fp and sync_file_to_modal(f_id, fp):
                                        r = m_forecast.remote(file_id=f_id, file_ext=os.path.splitext(fp)[1].lower(), date_col=d_col, value_col=v_col)
                                        return r["forecast"], r["decomposition"]
                                t_path = f"/tmp/{f_id}_forecast.csv"
                                d_frame[[d_col, v_col]].to_csv(t_path, index=False)
                                forecaster = PriceForecaster(t_path, date_column=d_col, price_column=v_col)
                                forecaster.load_data(); forecaster.train_model()
                                f_df = forecaster.predict_next_months(3); dec = forecaster.decompose_series()
                                if os.path.exists(t_path): os.remove(t_path)
                                return f_df.to_dict(orient="records") if not f_df.empty else [], dec
                            except Exception: return [], None
                        future_forecast = executor.submit(_run_forecast_wrapper, file_id, date_col, value_col, df)

                # 2. Collect base results
                if future_audit:
                    try:
                        ra = future_audit.result()
                        if ra and isinstance(ra, dict) and "error" not in ra:
                            anomalies = [AnomalyAlert(**a) for a in ra.get("anomalies", [])]
                            data_quality = DataQualityReport(**ra.get("quality", {}))
                    except Exception as e:
                        logger.error(f"Modal audit failed: {e}")
                
                if not data_quality: data_quality = calculate_data_quality(df)
                if not anomalies: anomalies = detect_anomalies(df)
                    
                correlations = future_corr.result()
                feature_importance = future_feat.result()
                segments = future_segments.result()
                
                if future_forecast:
                    try:
                        f_res = future_forecast.result()
                        if f_res and len(f_res) == 2:
                            _, time_series_decomp = f_res
                    except Exception as e:
                        logger.error(f"Forecasting failed: {e}")

            # --- Summary Stat & Profile Setup ---
            row_count = len(df)
            profile_parts = [("High-Volume" if row_count > 100 else "Micro-Dataset")]
            quality_score = data_quality.score if data_quality else 100.0
            profile_parts.append("Unrefined" if (quality_score < 80 or len(anomalies) > (row_count * 0.05)) else "Refined")
            detection_profile = " | ".join(profile_parts)

            summary_stats = {
                "total_rows": row_count,
                "total_columns": len(df.columns),
                "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
                "categorical_columns": df.select_dtypes(include="object").columns.tolist(),
            }

            # --- P&L Calculation (Robust) ---
            import re
            rev_patterns = [r"revenue", r"sales", r"income", r"total.?val", r"turnover"]
            cost_patterns = [r"cost", r"expense", r"spending", r"outgo", r"total.?cost"]
            
            rev_c = next((c for c in df.columns if any(re.search(p, str(c), re.I) for p in rev_patterns)), None)
            cost_c = next((c for c in df.columns if any(re.search(p, str(c), re.I) for p in cost_patterns)), None)
            if rev_c and cost_c:
                try:
                    total_rev = safe_float(df[rev_c].sum()); total_cost = safe_float(df[cost_c].sum())
                    net_profit = total_rev - total_cost
                    margin = (net_profit / total_rev * 100) if total_rev != 0 else 0
                    profit_loss = ProfitLossData(total_revenue=round(total_rev, 2), total_cost=round(total_cost, 2), net_profit=round(net_profit, 2), margin_percentage=round(safe_float(margin), 2))
                except Exception: pass
        else:
            data_info = f"Document text (first 4000 chars):\n{text[:4000]}"
            summary_stats = {"document_length": len(text), "type": "unstructured"}

        pl_context = f"\nFinancial Stats: Revenue={profit_loss.total_revenue}, Cost={profit_loss.total_cost}, Profit={profit_loss.net_profit}, Margin={profit_loss.margin_percentage}%" if profit_loss else ""
        ds_context = f"\nKey Correlations: {len(correlations)} analyzed.\nData Anomalies: {len(anomalies)} detected."

        # Synthesizer Prompt Preparation
        prompt_data = f"{data_info}\n{pl_context}\n{ds_context}"

        # --- Multi-Agent Swarm (Parallel) ---
        agents_cfg = {
            "CFO": {"role": "CFO Persona", "focus": "Analyze financial efficiency."},
            "Risk": {"role": "Risk Assessor Persona", "focus": "Analyze anomalies and risks."},
            "CMO": {"role": "CMO Persona", "focus": "Analyze market segments."}
        }
        agent_responses = {}
        def run_agent_task(name, cfg_item):
            try:
                m_agent = get_modal_func("run_agent_analysis")
                if m_agent: return name, m_agent.remote(cfg_item['role'], cfg_item['focus'], prompt_data)
                ai_c = _get_client(settings.OPENAI_API_KEY)
                r = ai_c.chat.completions.create(model=settings.ANALYSIS_MODEL, messages=[{"role": "system", "content": f"You are the {cfg_item['role']}. {cfg_item['focus']}"}, {"role": "user", "content": f"Data:\n{prompt_data}"}], temperature=0.4)
                return name, r.choices[0].message.content
            except Exception: return name, "Analysis unavailable."

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            fut_agents = [executor.submit(run_agent_task, n, c) for n, c in agents_cfg.items()]
            for f in concurrent.futures.as_completed(fut_agents):
                name, output = f.result()
                agent_responses[name] = output
                agent_insights.append(AgentInsight(agent_role=name, report=output))

        # Synthesizer
        s_prompt = f"Executive Synthesis from CFO: {agent_responses.get('CFO')} | Risk: {agent_responses.get('Risk')} | CMO: {agent_responses.get('CMO')}\nData Context: {data_info}"

        system_prompt = "You are the Executive Synthesizer AI. Return valid JSON only."

        try:
            response = client.chat.completions.create(
                model=settings.ANALYSIS_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": s_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            result = json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI API call failed for dashboard synthesis: {e}")
            result = {"charts": [], "growth_suggestions": []}

        charts = []
        charts_json = result.get("charts", [])
        if not isinstance(charts_json, list):
            charts_json = []

        for c in charts_json:
            if isinstance(c, dict):
                charts.append(ChartSuggestion(
                    chart_type=str(c.get("chart_type", "bar")),
                    title=str(c.get("title", "Data Visualization")),
                    description=str(c.get("description", "")),
                    x_axis=c.get("x_axis"),
                    y_axis=c.get("y_axis"),
                    data=c.get("data", []) if isinstance(c.get("data"), list) else [],
                ))

        growth_suggestions = []
        suggestions_json = result.get("growth_suggestions", [])
        if not isinstance(suggestions_json, list):
            suggestions_json = []

        for s in suggestions_json:
            if isinstance(s, dict):
                growth_suggestions.append(GrowthSuggestion(
                    title=str(s.get("title", "Strategic Recommendation")),
                    description=str(s.get("description", "")),
                    impact=str(s.get("impact", "Medium")),
                    feasibility=str(s.get("feasibility", "Medium"))
                ))


        return DashboardResponse(
            file_id=file_id, 
            detection_profile=detection_profile,
            charts=cleanup_serializable(charts), 
            summary_stats=cleanup_serializable(summary_stats),
            profit_loss=cleanup_serializable(profit_loss) if profit_loss else None,
            growth_suggestions=cleanup_serializable(growth_suggestions),
            correlations=cleanup_serializable(correlations) if correlations else None,
            anomalies=cleanup_serializable(anomalies) if anomalies else None,
            data_quality=cleanup_serializable(data_quality) if data_quality else None,
            feature_importance=cleanup_serializable(feature_importance) if feature_importance else None,
            segments=cleanup_serializable(segments) if segments else None,
            time_series_decomposition=cleanup_serializable(time_series_decomp) if time_series_decomp else None,
            agent_insights=cleanup_serializable(agent_insights) if agent_insights else None
        )
    except Exception as e:
        logger.exception(f"Error generating dashboard for file {file_id}")
        raise e
