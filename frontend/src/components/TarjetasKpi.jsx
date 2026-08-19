import React from "react";
import { Users, Award, TrendingUp, ThumbsUp } from "lucide-react";

export default function TarjetasKpi({ kpis }) {
  if (!kpis) return null;

  const {
    total_surveys = 0,
    overall_average = 0,
    nps = 0,
    satisfaction_pct = 0,
    promoters_pct = 0,
    detractors_pct = 0,
  } = kpis;

  const obtenerEtiquetaNps = (score) => {
    if (score >= 50) return { etiqueta: "Excelente", fondo: "var(--success-bg)", texto: "var(--success)" };
    if (score >= 0) return { etiqueta: "Bueno", fondo: "var(--warning-bg)", texto: "var(--warning)" };
    return { etiqueta: "A mejorar", fondo: "var(--danger-bg)", texto: "var(--danger)" };
  };

  const badgeNps = obtenerEtiquetaNps(nps);

  return (
    <div className="kpi-grid">
      {/* 1. Total Encuestas */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">Total Respuestas</span>
          <div className="kpi-icon" style={{ backgroundColor: "var(--primary-light)", color: "var(--primary)" }}>
            <Users size={20} />
          </div>
        </div>
        <div className="kpi-value">{total_surveys.toLocaleString()}</div>
        <div className="kpi-subtext">
          <span>Encuestas procesadas</span>
        </div>
      </div>

      {/* 2. Promedio General */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">Promedio General</span>
          <div className="kpi-icon" style={{ backgroundColor: "#fef3c7", color: "#d97706" }}>
            <Award size={20} />
          </div>
        </div>
        <div className="kpi-value">
          {overall_average.toFixed(1)}
          <span style={{ fontSize: "1.1rem", color: "var(--text-muted)", fontWeight: 500 }}> / 10</span>
        </div>
        <div className="kpi-subtext">
          <span>Promedio global preguntas Q01 a Q08</span>
        </div>
      </div>

      {/* 3. NPS Score */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">NPS (Recomendación)</span>
          <div className="kpi-icon" style={{ backgroundColor: "var(--success-bg)", color: "var(--success)" }}>
            <TrendingUp size={20} />
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem" }}>
          <div className="kpi-value">
            {nps > 0 ? `+${nps.toFixed(0)}` : nps.toFixed(0)}
          </div>
          <span className="badge" style={{ backgroundColor: badgeNps.fondo, color: badgeNps.texto }}>
            {badgeNps.etiqueta}
          </span>
        </div>
        <div className="kpi-subtext">
          <span>{promoters_pct}% Promotores / {detractors_pct}% Detractores</span>
        </div>
      </div>

      {/* 4. Índice de Satisfacción */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">Satisfacción General</span>
          <div className="kpi-icon" style={{ backgroundColor: "#ede9fe", color: "#7c3aed" }}>
            <ThumbsUp size={20} />
          </div>
        </div>
        <div className="kpi-value">{satisfaction_pct.toFixed(1)}%</div>
        <div className="kpi-subtext">
          <span>Respuestas con nota 8 o superior en Q06</span>
        </div>
      </div>
    </div>
  );
}
