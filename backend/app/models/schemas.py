from pydantic import BaseModel


# --- File Upload ---

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    num_chunks: int
    preview: str


# --- Analysis ---

class AnalysisRequest(BaseModel):
    file_id: str
    custom_prompt: str | None = None
    language: str | None = None


class AnalysisResponse(BaseModel):
    file_id: str
    summary: str
    key_insights: list[str]
    trends: list[str]
    recommendations: list[str]
    data_stats: dict | None = None


# --- Chat ---

class ChatRequest(BaseModel):
    file_id: str
    question: str
    session_id: str | None = None
    chat_history: list[dict] = []
    language: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    session_id: str


class ChatSession(BaseModel):
    session_id: str
    file_id: str
    title: str
    messages: list[dict]
    created_at: str
    updated_at: str


# --- Dashboard ---

class ChartSuggestion(BaseModel):
    chart_type: str
    title: str
    description: str
    x_axis: str | None = None
    y_axis: str | None = None
    data: list[dict]


class ProfitLossData(BaseModel):
    total_revenue: float
    total_cost: float
    net_profit: float
    margin_percentage: float


class GrowthSuggestion(BaseModel):
    title: str
    description: str
    impact: str
    feasibility: str


class CorrelationMetric(BaseModel):
    column_a: str
    column_b: str
    correlation: float
    description: str


class AnomalyAlert(BaseModel):
    column: str
    row_index: int
    value: float
    reason: str

class DataQualityReport(BaseModel):
    score: float
    missing_values_count: int
    duplicates_count: int
    variance_score: float
    issues: list[str]

class FeatureImportanceMetric(BaseModel):
    feature_name: str
    importance_score: float
    impact_level: str # High, Medium, Low
    contribution_type: str # Positive, Negative, Neutral

class DataSegment(BaseModel):
    name: str
    size: int
    characteristics: str
    growth_strategy: str

class TimeSeriesDecomposition(BaseModel):
    dates: list[str]
    observed: list[float]
    trend: list[float]
    seasonal: list[float]
    residual: list[float]

class DashboardResponse(BaseModel):
    file_id: str
    detection_profile: str | None = None
    charts: list[ChartSuggestion]
    summary_stats: dict
    profit_loss: ProfitLossData | None = None
    growth_suggestions: list[GrowthSuggestion] | None = None
    correlations: list[CorrelationMetric] | None = None
    anomalies: list[AnomalyAlert] | None = None
    data_quality: DataQualityReport | None = None
    feature_importance: list[FeatureImportanceMetric] | None = None
    segments: list[DataSegment] | None = None
    time_series_decomposition: TimeSeriesDecomposition | None = None


# --- Multi-file Comparison ---

class CompareRequest(BaseModel):
    file_ids: list[str]
    custom_prompt: str | None = None
    language: str | None = None


class CompareResponse(BaseModel):
    comparison_summary: str
    similarities: list[str]
    differences: list[str]
    metrics_delta: dict[str, float] | None = None
    comparative_strategy: str | None = None
    file_summaries: dict[str, str]


# --- Data Cleaning ---

class CleaningIssue(BaseModel):
    column: str
    issue_type: str
    severity: str
    description: str
    suggestion: str
    affected_rows: int


class DataCleaningResponse(BaseModel):
    file_id: str
    total_issues: int
    quality_score: float
    issues: list[CleaningIssue]
    ai_recommendations: list[str]


# --- Sharing ---

class ShareRequest(BaseModel):
    file_id: str
    include_analysis: bool = True
    include_dashboard: bool = True
    expires_hours: int = 72


class ShareResponse(BaseModel):
    share_id: str
    share_url: str
    expires_at: str


class SharedReportResponse(BaseModel):
    filename: str
    analysis: AnalysisResponse | None
    dashboard: DashboardResponse | None
    created_at: str


# --- File Library ---

class FileRecord(BaseModel):
    file_id: str
    filename: str
    file_type: str
    num_chunks: int
    uploaded_at: str
    file_size: int


# --- Language Detection ---

class LanguageDetectResponse(BaseModel):
    file_id: str
    detected_language: str
    confidence: float


# --- Email Report ---

class EmailReportRequest(BaseModel):
    file_id: str
    email: str
    include_charts: bool = True


# --- API Key Management ---

class ApiKeyRequest(BaseModel):
    openai_api_key: str


class ApiKeyStatus(BaseModel):
    has_key: bool
    key_preview: str


# --- Forecasting ---

class ForecastRequest(BaseModel):
    file_id: str
    date_column: str = "Date"
    price_column: str = "Price"
    months: int = 3


class ForecastDataPoint(BaseModel):
    date: str
    price: float


class ForecastResponse(BaseModel):
    file_id: str
    forecast: list[ForecastDataPoint]
    metrics: dict
