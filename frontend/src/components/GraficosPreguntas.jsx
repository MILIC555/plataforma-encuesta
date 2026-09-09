import React, { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { BarChart3, Info } from "lucide-react";

export default function GraficosPreguntas({ datosPreguntas }) {
  const [tipoGrafico, setTipoGrafico] = useState("bar"); // "bar" | "radar"

  if (!datosPreguntas || datosPreguntas.length === 0) return null;

  const datosFormateados = datosPreguntas.map((q) => ({
    numero: `Q0${q.question_number}`,
    nombre: q.short_label,
    nombreCompleto: q.description,
    promedio: q.average,
    cantidad: q.count,
    textOptions: q.text_options || [],
    textCount: q.text_count || 0,
  }));

  const TooltipPersonalizado = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ background: "white", padding: "0.85rem", border: "1px solid var(--border-color)", borderRadius: "8px", boxShadow: "var(--shadow-md)", maxWidth: "320px" }}>
          <p style={{ fontWeight: 700, color: "var(--text-main)", marginBottom: "0.35rem" }}>
            {data.numero}: {data.nombre}
          </p>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.6rem" }}>
            "{data.nombreCompleto}"
          </p>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--border-color)", paddingTop: "0.4rem" }}>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Calificación Promedio:</span>
            <strong style={{ fontSize: "1.1rem", color: "var(--primary)" }}>{data.promedio} / 10</strong>
          </div>
          {data.textOptions && data.textOptions.length > 0 && (
            <div style={{ marginTop: "0.4rem", borderTop: "1px dashed var(--border-color)", paddingTop: "0.4rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
              {data.textOptions.map((opt, idx) => (
                <div key={idx} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{opt.label}:</span>
                  <strong>{opt.count} resp.</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <BarChart3 size={20} style={{ color: "var(--primary)" }} />
            <span>Desempeño por Dimensión ({datosPreguntas.length} Preguntas Evaluadas)</span>
          </h3>
          <p className="card-subtitle">
            Calificación en escala del 1 al 10 e incidencias no numéricas
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            className={`btn btn-sm ${tipoGrafico === "bar" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setTipoGrafico("bar")}
          >
            Barras
          </button>
          <button
            className={`btn btn-sm ${tipoGrafico === "radar" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setTipoGrafico("radar")}
          >
            Radar
          </button>
        </div>
      </div>

      <div style={{ height: "320px", width: "100%", marginTop: "1rem" }}>
        <ResponsiveContainer width="100%" height="100%">
          {tipoGrafico === "bar" ? (
            <BarChart data={datosFormateados} margin={{ top: 10, right: 20, left: -10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="nombre" angle={-15} textAnchor="end" tick={{ fontSize: 12, fill: "#475569" }} />
              <YAxis domain={[0, 10]} ticks={[0, 2, 4, 6, 8, 10]} tick={{ fontSize: 12, fill: "#475569" }} />
              <Tooltip content={<TooltipPersonalizado />} />
              <Bar dataKey="promedio" fill="#3b82f6" radius={[6, 6, 0, 0]} />
            </BarChart>
          ) : (
            <RadarChart outerRadius={110} data={datosFormateados}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="nombre" tick={{ fontSize: 11, fill: "#475569" }} />
              <PolarRadiusAxis domain={[0, 10]} angle={30} stroke="#94a3b8" />
              <Radar name="Promedio" dataKey="promedio" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.4} />
              <Tooltip content={<TooltipPersonalizado />} />
            </RadarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Resumen inferior con badges para opciones textuales */}
      <div style={{ marginTop: "1.5rem", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.75rem" }}>
        {datosPreguntas.map((q) => (
          <div
            key={`${q.platform || 'p'}-${q.question_number}`}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.35rem",
              padding: "0.75rem 0.95rem",
              background: "var(--bg-main)",
              borderRadius: "8px",
              border: "1px solid var(--border-color)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span style={{ fontWeight: 700, fontSize: "0.8rem", color: "var(--primary)", background: "var(--primary-light)", padding: "0.15rem 0.4rem", borderRadius: "4px" }}>
                  Q0{q.question_number}
                </span>
                <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-main)" }}>
                  {q.short_label}
                </span>
              </div>
              <strong style={{ fontSize: "0.95rem", color: q.average >= 9 ? "var(--success)" : q.average >= 7 ? "var(--primary)" : "var(--warning)" }}>
                {q.average.toFixed(2)}
              </strong>
            </div>

            {/* Opciones textuales especiales si existen (ej. 'No me comuniqué con el tutor') */}
            {q.text_options && q.text_options.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem", marginTop: "0.2rem" }}>
                {q.text_options.map((opt, oIdx) => (
                  <span
                    key={oIdx}
                    className="badge badge-neutral"
                    style={{ fontSize: "0.7rem", display: "flex", alignItems: "center", gap: "0.25rem" }}
                    title={`Opción especial seleccionada por ${opt.count} participante(s)`}
                  >
                    <Info size={11} />
                    <span>{opt.label}: <strong>{opt.count}</strong></span>
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
