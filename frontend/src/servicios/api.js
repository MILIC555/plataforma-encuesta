const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchHealth() {
  const res = await fetch(`${API_URL}/health`);
  return res.json();
}

export async function fetchKpis(filters = {}) {
  const params = new URLSearchParams();
  if (filters.course_id) params.append("course_id", filters.course_id);
  if (filters.platform && filters.platform !== "todos") params.append("platform", filters.platform);
  if (filters.start_date) params.append("start_date", filters.start_date);
  if (filters.end_date) params.append("end_date", filters.end_date);
  const res = await fetch(`${API_URL}/api/dashboard/kpis?${params}`);
  return res.json();
}

export async function fetchQuestions(filters = {}) {
  const params = new URLSearchParams();
  if (filters.course_id) params.append("course_id", filters.course_id);
  if (filters.platform && filters.platform !== "todos") params.append("platform", filters.platform);
  if (filters.start_date) params.append("start_date", filters.start_date);
  if (filters.end_date) params.append("end_date", filters.end_date);
  const res = await fetch(`${API_URL}/api/dashboard/questions?${params}`);
  return res.json();
}

export async function fetchCourses() {
  const res = await fetch(`${API_URL}/api/surveys/courses`);
  return res.json();
}

export async function fetchCoursesComparison(filters = {}) {
  const params = new URLSearchParams();
  if (filters.platform && filters.platform !== "todos") params.append("platform", filters.platform);
  if (filters.start_date) params.append("start_date", filters.start_date);
  if (filters.end_date) params.append("end_date", filters.end_date);
  const res = await fetch(`${API_URL}/api/dashboard/courses?${params}`);
  return res.json();
}

export async function fetchTrends(filters = {}) {
  const params = new URLSearchParams();
  if (filters.course_id) params.append("course_id", filters.course_id);
  if (filters.platform && filters.platform !== "todos") params.append("platform", filters.platform);
  const res = await fetch(`${API_URL}/api/dashboard/trends?${params}`);
  return res.json();
}

export async function fetchAiInsights(filters = {}) {
  const params = new URLSearchParams();
  if (filters.course_id) params.append("course_id", filters.course_id);
  if (filters.platform && filters.platform !== "todos") params.append("platform", filters.platform);
  if (filters.start_date) params.append("start_date", filters.start_date);
  if (filters.end_date) params.append("end_date", filters.end_date);
  const res = await fetch(`${API_URL}/api/dashboard/ai-insights?${params}`);
  return res.json();
}

export async function fetchComments(filters = {}) {
  const params = new URLSearchParams();
  if (filters.course_id) params.append("course_id", filters.course_id);
  if (filters.platform && filters.platform !== "todos") params.append("platform", filters.platform);
  if (filters.topic && filters.topic !== "todos") params.append("topic", filters.topic);
  if (filters.sentiment && filters.sentiment !== "todos") params.append("sentiment", filters.sentiment);
  if (filters.search) params.append("search", filters.search);
  if (filters.page) params.append("page", filters.page);
  params.append("page_size", filters.page_size || 50);

  const res = await fetch(`${API_URL}/api/dashboard/comments?${params}`);
  return res.json();
}

export async function uploadSurveyFiles(files) {
  const formData = new FormData();
  const fileList = Array.isArray(files) ? files : [files];
  for (const f of fileList) {
    formData.append("files", f);
  }
  const res = await fetch(`${API_URL}/api/surveys/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Error al subir los archivos");
  }
  return res.json();
}

export const uploadSurveyFile = uploadSurveyFiles;

export async function deleteCourse(courseId) {
  const res = await fetch(`${API_URL}/api/surveys/courses/${courseId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Error al eliminar el curso");
  }
  return res.json();
}

export async function clearAllSurveys() {
  const res = await fetch(`${API_URL}/api/surveys/clear-all`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Error al vaciar las encuestas");
  }
  return res.json();
}

export async function triggerAiAnalysis() {
  const res = await fetch(`${API_URL}/api/ai/analyze-comments`, {
    method: "POST",
  });
  return res.json();
}

export function getExportPdfUrl(filters = {}) {
  const params = new URLSearchParams();
  if (filters.course_id) params.append("course_id", filters.course_id);
  if (filters.platform && filters.platform !== "todos") params.append("platform", filters.platform);
  if (filters.start_date) params.append("start_date", filters.start_date);
  if (filters.end_date) params.append("end_date", filters.end_date);
  return `${API_URL}/api/reports/pdf?${params}`;
}

export function getExportExcelUrl(filters = {}) {
  const params = new URLSearchParams();
  if (filters.course_id) params.append("course_id", filters.course_id);
  if (filters.platform && filters.platform !== "todos") params.append("platform", filters.platform);
  if (filters.start_date) params.append("start_date", filters.start_date);
  if (filters.end_date) params.append("end_date", filters.end_date);
  return `${API_URL}/api/reports/excel?${params}`;
}

export async function downloadExportPdf(filters = {}) {
  const url = getExportPdfUrl(filters);
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("No se pudo generar el reporte PDF. Por favor intente más tarde.");
  }
  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  const fechaStr = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  link.download = `reporte_encuestas_${fechaStr}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

export async function downloadExportExcel(filters = {}) {
  const url = getExportExcelUrl(filters);
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("No se pudo generar la planilla Excel. Por favor intente más tarde.");
  }
  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  const fechaStr = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  link.download = `datos_encuestas_${fechaStr}.xlsx`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

