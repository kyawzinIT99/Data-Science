import axios from "axios";

const api = axios.create({ baseURL: "/api", timeout: 600000 });

// --- Auth Interceptors ---
if (typeof window !== "undefined") {
  api.interceptors.request.use((config) => {
    const token = localStorage.getItem("kyawzin_access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem("kyawzin_access_token");
        if (typeof window !== "undefined") {
          // If not a shared link page, we might want to signal a logout/re-auth
          // For now, let the component state handle it via localstorage changes
        }
      }
      return Promise.reject(error);
    }
  );
}

// --- Types ---

export interface FileUploadResponse {
  file_id: string;
  filename: string;
  file_type: string;
  num_chunks: number;
  preview: string;
}

export interface FileRecord {
  file_id: string;
  filename: string;
  file_type: string;
  num_chunks: number;
  uploaded_at: string;
  file_size: number;
}

export interface AnalysisResponse {
  file_id: string;
  summary: string;
  key_insights: string[];
  trends: string[];
  recommendations: string[];
  data_stats: Record<string, any> | null;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  session_id: string;
}

export interface ChatSessionInfo {
  session_id: string;
  file_id: string;
  title: string;
  messages: { role: string; content: string }[];
  created_at: string;
  updated_at: string;
}

export interface ChartData {
  chart_type: string;
  title: string;
  description: string;
  x_axis: string | null;
  y_axis: string | null;
  data: Record<string, any>[];
}

export interface ProfitLossData {
  total_revenue: number;
  total_cost: number;
  net_profit: number;
  margin_percentage: number;
}

export interface GrowthSuggestion {
  title: string;
  description: string;
  impact: string;
  feasibility: string;
}

export interface CorrelationMetric {
  column_a: string;
  column_b: string;
  correlation: number;
  description: string;
}

export interface AnomalyAlert {
  column: string;
  row_index: number;
  value: number;
  reason: string;
}

export interface DataSegment {
  name: string;
  size: number;
  characteristics: string;
  growth_strategy: string;
}

export interface AgentInsight {
  agent_role: string;
  report: string;
}

export interface DashboardResponse {
  file_id: string;
  detection_profile?: string;
  charts: ChartData[];
  summary_stats: Record<string, any>;
  profit_loss: ProfitLossData | null;
  growth_suggestions: GrowthSuggestion[] | null;
  correlations?: CorrelationMetric[];
  anomalies?: AnomalyAlert[];
  data_quality?: DataQualityReport;
  feature_importance?: FeatureImportanceMetric[];
  segments?: DataSegment[];
  time_series_decomposition?: TimeSeriesDecomposition | null;
  agent_insights?: AgentInsight[];
}

export interface TimeSeriesDecomposition {
  dates: string[];
  observed: number[];
  trend: number[];
  seasonal: number[];
  residual: number[];
}

export interface DataSegment {
  name: string;
  size: number;
  characteristics: string;
  growth_strategy: string;
}

export interface DataQualityReport {
  score: number;
  missing_values_count: number;
  duplicates_count: number;
  variance_score: number;
  issues: string[];
}

export interface FeatureImportanceMetric {
  feature_name: string;
  importance_score: number;
  impact_level: string;
  contribution_type: string;
}

export interface CompareResponse {
  comparison_summary: string;
  similarities: string[];
  differences: string[];
  metrics_delta?: Record<string, number>;
  comparative_strategy?: string;
  file_summaries: Record<string, string>;
}

export interface CleaningIssue {
  column: string;
  issue_type: string;
  severity: string;
  description: string;
  suggestion: string;
  affected_rows: number;
}

export interface DataCleaningResponse {
  file_id: string;
  total_issues: number;
  quality_score: number;
  issues: CleaningIssue[];
  ai_recommendations: string[];
}

export interface ShareResponse {
  share_id: string;
  share_url: string;
  expires_at: string;
}

export interface SharedReportResponse {
  filename: string;
  analysis: AnalysisResponse | null;
  dashboard: DashboardResponse | null;
  created_at: string;
}

// --- Causal Inference ---

export interface CausalNode {
  id: string;
  group: number;
}
export interface CausalLink {
  source: string;
  target: string;
  value: number;
  strength: string;
}
export interface CausalNetwork {
  nodes: CausalNode[];
  links: CausalLink[];
  error: string | null;
}

export async function getCausalNetwork(fileId: string): Promise<CausalNetwork> {
  const res = await api.get(`/causal/${fileId}`);
  return res.data;
}

// --- File Upload & Library ---

export async function uploadFile(file: File): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function uploadMultiFile(files: File[]): Promise<FileUploadResponse> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append("files", file);
  });
  const res = await api.post("/upload-multi", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function listFiles(): Promise<FileRecord[]> {
  const res = await api.get("/files");
  return res.data;
}

export async function deleteFile(fileId: string): Promise<void> {
  await api.delete(`/files/${fileId}`);
}

// --- Analysis (with optional custom prompt) ---

export async function analyzeFile(fileId: string, customPrompt?: string, language?: string): Promise<AnalysisResponse> {
  const res = await api.post("/analyze", {
    file_id: fileId,
    custom_prompt: customPrompt || null,
    language: language || null
  });
  return res.data;
}

export async function getDashboard(fileId: string, language?: string): Promise<DashboardResponse> {
  const res = await api.post("/dashboard", { file_id: fileId, language: language || null });
  return res.data;
}

// --- QA & Auto-Refinement ---

export interface QAResponse {
  score: number;
  requires_refinement: boolean;
  issues: string[];
  row_count: number;
  col_count: number;
}

export interface RefineResponse {
  success: boolean;
  message: string;
  final_rows: number;
}

export async function checkDataQuality(fileId: string): Promise<QAResponse> {
  const res = await api.post("/qa", { file_id: fileId });
  return res.data;
}

export async function refineDataset(fileId: string): Promise<RefineResponse> {
  const res = await api.post("/refine", { file_id: fileId });
  return res.data;
}

// --- Chat (with session support) ---

export async function chatWithFile(
  fileId: string,
  question: string,
  chatHistory: { role: string; content: string }[],
  sessionId?: string,
  language?: string
): Promise<ChatResponse> {
  const res = await api.post("/chat", {
    file_id: fileId,
    question,
    chat_history: chatHistory,
    session_id: sessionId || null,
    language: language || null,
  });
  return res.data;
}

export async function getChatSessions(fileId: string): Promise<ChatSessionInfo[]> {
  const res = await api.get(`/chat/sessions/${fileId}`);
  return res.data;
}

export async function getChatSession(sessionId: string): Promise<ChatSessionInfo> {
  const res = await api.get(`/chat/session/${sessionId}`);
  return res.data;
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await api.delete(`/chat/session/${sessionId}`);
}

// --- Multi-file Comparison ---

export async function compareFiles(fileIds: string[], customPrompt?: string, language?: string): Promise<CompareResponse> {
  const res = await api.post("/compare", {
    file_ids: fileIds,
    custom_prompt: customPrompt || null,
    language: language || null
  });
  return res.data;
}

// --- Data Cleaning ---

export async function getDataCleaning(fileId: string): Promise<DataCleaningResponse> {
  const res = await api.post("/clean", { file_id: fileId });
  return res.data;
}

// --- Sharing ---

export async function createShare(
  fileId: string,
  includeAnalysis = true,
  includeDashboard = true,
  expiresHours = 72
): Promise<ShareResponse> {
  const res = await api.post("/share", {
    file_id: fileId,
    include_analysis: includeAnalysis,
    include_dashboard: includeDashboard,
    expires_hours: expiresHours,
  });
  return res.data;
}

export async function getSharedReport(shareId: string): Promise<SharedReportResponse> {
  const res = await api.get(`/shared/${shareId}`);
  return res.data;
}

// --- Export ---

export async function exportPdfReport(fileId: string, includeCharts = true): Promise<void> {
  const res = await api.get(`/export/${fileId}/pdf`, {
    params: { include_charts: includeCharts },
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `analysis_report_${fileId.slice(0, 8)}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function exportPptxReport(fileId: string, includeCharts = true): Promise<void> {
  const res = await api.get(`/export/${fileId}/pptx`, {
    params: { include_charts: includeCharts },
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `analysis_report_${fileId.slice(0, 8)}.pptx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function exportJsonReport(fileId: string): Promise<void> {
  const res = await api.get(`/export/${fileId}/json`);
  const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `analysis_report_${fileId.slice(0, 8)}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

// --- Language Detection ---

export interface LanguageDetectResponse {
  file_id: string;
  detected_language: string;
  confidence: number;
}

export async function detectLanguage(fileId: string): Promise<LanguageDetectResponse> {
  const res = await api.post("/detect-language", { file_id: fileId });
  return res.data;
}

// --- Email Reports ---

export async function emailReport(fileId: string, email: string, includeCharts = true): Promise<void> {
  await api.post("/email-report", { file_id: fileId, email, include_charts: includeCharts });
}

// --- API Key Management ---

export interface ApiKeyStatus {
  has_key: boolean;
  key_preview: string;
}

export async function getApiKeyStatus(): Promise<ApiKeyStatus> {
  const res = await api.get("/settings/api-key");
  return res.data;
}

export async function setApiKey(key: string): Promise<ApiKeyStatus> {
  const res = await api.post("/settings/api-key", { openai_api_key: key });
  return res.data;
}

export async function removeApiKey(): Promise<void> {
  await api.delete("/settings/api-key");
}

// --- Auth ---

export async function login(username: string, password: string): Promise<{ access_token: string }> {
  const res = await api.post("/login", { username, password });
  if (res.data.access_token) {
    localStorage.setItem("kyawzin_access_token", res.data.access_token);
  }
  return res.data;
}
