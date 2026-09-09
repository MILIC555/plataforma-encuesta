import React from "react";
import { GraduationCap } from "lucide-react";

export default function TablaCursos({ comparacionCursos }) {
  if (!comparacionCursos || comparacionCursos.length === 0) return null;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <GraduationCap size={20} style={{ color: "var(--primary)" }} />
            <span>Comparativa de Rendimiento por Curso (Campus Córdoba)</span>
          </h3>
          <p className="card-subtitle">
            Ranking comparativo de satisfacción, NPS y volumen de respuestas
          </p>
        </div>
      </div>

      <div className="table-container">
        <table className="styled-table">
          <thead>
            <tr>
              <th>Curso</th>
              <th style={{ textAlign: "center" }}>Encuestas</th>
              <th style={{ textAlign: "center" }}>Promedio Global</th>
              <th style={{ textAlign: "center" }}>NPS Score</th>
              <th style={{ textAlign: "center" }}>Satisfacción</th>
            </tr>
          </thead>
          <tbody>
            {comparacionCursos.map((c) => (
              <tr key={c.id}>
                <td style={{ fontWeight: 600 }}>{c.name}</td>
                <td style={{ textAlign: "center", fontWeight: 700 }}>{c.total_surveys}</td>
                <td style={{ textAlign: "center" }}>
                  <span
                    style={{
                      fontWeight: 800,
                      color: c.overall_average >= 9 ? "var(--success)" : c.overall_average >= 7 ? "var(--primary)" : "var(--warning)",
                    }}
                  >
                    {c.overall_average.toFixed(1)}
                  </span>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}> / 10</span>
                </td>
                <td style={{ textAlign: "center" }}>
                  <span className="badge" style={{ backgroundColor: c.nps >= 50 ? "var(--success-bg)" : "var(--warning-bg)", color: c.nps >= 50 ? "var(--success)" : "var(--warning)" }}>
                    {c.nps > 0 ? `+${c.nps.toFixed(0)}` : c.nps.toFixed(0)}
                  </span>
                </td>
                <td style={{ textAlign: "center", fontWeight: 600 }}>{c.satisfaction_pct.toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
