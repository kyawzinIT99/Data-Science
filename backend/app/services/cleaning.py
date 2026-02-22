"""Data quality assessment and cleaning suggestions."""

import json
import numpy as np
import pandas as pd
from openai import OpenAI

from app.core.config import settings
from app.models.schemas import CleaningIssue, DataCleaningResponse
from app.utils.serialization import cleanup_serializable

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def assess_data_quality(file_id: str, df: pd.DataFrame) -> DataCleaningResponse:
    issues: list[CleaningIssue] = []

    # 1. Missing values
    for col in df.columns:
        missing = int(df[col].isnull().sum())
        total_rows = len(df)
        if missing > 0 and total_rows > 0:
            pct = missing / total_rows * 100
            severity = "high" if pct > 30 else "medium" if pct > 10 else "low"
            issues.append(CleaningIssue(
                column=col,
                issue_type="missing_values",
                severity=severity,
                description=f"{missing} missing values ({pct:.1f}%)",
                suggestion=f"Fill with median/mode or drop rows if {col} is non-critical",
                affected_rows=missing,
            ))

    # 2. Duplicates
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        issues.append(CleaningIssue(
            column="[all]",
            issue_type="duplicates",
            severity="medium" if dup_count > len(df) * 0.05 else "low",
            description=f"{dup_count} duplicate rows found",
            suggestion="Remove duplicate rows with df.drop_duplicates()",
            affected_rows=dup_count,
        ))

    # 3. Outliers in numeric columns (IQR method)
    for col in df.select_dtypes(include="number").columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = int(((df[col] < lower) | (df[col] > upper)).sum())
        if outliers > 0:
            issues.append(CleaningIssue(
                column=col,
                issue_type="outliers",
                severity="medium" if outliers > len(df) * 0.05 else "low",
                description=f"{outliers} potential outliers (outside IQR bounds: {lower:.2f} to {upper:.2f})",
                suggestion=f"Investigate outliers — clip, winsorize, or remove if erroneous",
                affected_rows=outliers,
            ))

    # 4. Mixed types / formatting issues in object columns
    for col in df.select_dtypes(include="object").columns:
        # Check if column looks numeric but stored as string
        numeric_count = pd.to_numeric(df[col], errors="coerce").notna().sum()
        total_non_null = df[col].notna().sum()
        if total_non_null > 0 and numeric_count / total_non_null > 0.5 and numeric_count != total_non_null:
            bad_rows = int(total_non_null - numeric_count)
            issues.append(CleaningIssue(
                column=col,
                issue_type="type_mismatch",
                severity="medium",
                description=f"Column appears numeric but has {bad_rows} non-numeric values",
                suggestion=f"Convert to numeric with pd.to_numeric(errors='coerce') and handle NaN results",
                affected_rows=bad_rows,
            ))

        # Check leading/trailing whitespace
        if df[col].dtype == object:
            stripped = df[col].dropna().str.strip()
            whitespace_issues = int((df[col].dropna() != stripped).sum())
            if whitespace_issues > 0:
                issues.append(CleaningIssue(
                    column=col,
                    issue_type="formatting",
                    severity="low",
                    description=f"{whitespace_issues} values have leading/trailing whitespace",
                    suggestion=f"Strip whitespace: df['{col}'] = df['{col}'].str.strip()",
                    affected_rows=whitespace_issues,
                ))

    # Calculate quality score
    total_cells = len(df) * len(df.columns)
    total_affected = sum(i.affected_rows for i in issues)
    
    if total_cells == 0:
        quality_score = 100.0
    else:
        quality_score = max(0, 100 - (total_affected / total_cells) * 100)

    # Get AI recommendations
    ai_recs = _get_ai_recommendations(df, issues)

    return cleanup_serializable(DataCleaningResponse(
        file_id=file_id,
        total_issues=len(issues),
        quality_score=round(quality_score, 1),
        issues=issues,
        ai_recommendations=ai_recs,
    ))


def _get_ai_recommendations(df: pd.DataFrame, issues: list[CleaningIssue]) -> list[str]:
    issues_summary = "\n".join(
        f"- {i.column}: {i.issue_type} - {i.description}" for i in issues[:15]
    )

    prompt = f"""Given this dataset with {len(df)} rows and {len(df.columns)} columns:
Columns: {df.columns.tolist()}
Types: {df.dtypes.to_string()}

Issues found:
{issues_summary}

Provide 3-5 specific, actionable data cleaning recommendations. Focus on practical steps."""

    response = client.chat.completions.create(
        model=settings.ANALYSIS_MODEL,
        messages=[
            {"role": "system", "content": "You are a data quality expert. Give concise, practical cleaning advice. Return JSON with key 'recommendations' as a list of strings."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    result = json.loads(response.choices[0].message.content)
    return result.get("recommendations", [])
