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
import { BarChart3 } from "lucide-react";

export default function GraficosPreguntas({ datosPreguntas }) {
  const [tipoGrafico, setTipoGrafico] = useState("bar"); // "bar" | "radar"

  if (!datosPreguntas || datosPreguntas.length === 0) return null;

  const datosFormateados = datosPreguntas.map((q) => ({
    numero: `Q0${q.question_number}`,
    nombre: q.short_label,
    nombreCompleto: q.description,
    promedio: q.average,
    cantidad: q.count,
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
            <span>Desempeño por Dimensión (Preguntas Q01 a Q08)</span>
          </h3>
          <p className="card-subtitle">
            Evaluación detallada en escala del 1 al 10 para cada aspecto del curso
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

      {/* Resumen inferior */}
      <div style={{ marginTop: "1.5rem", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "0.75rem" }}>
        {datosPreguntas.map((q) => (
          <div
            key={q.question_number}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0.6rem 0.85rem",
              background: "var(--bg-main)",
              borderRadius: "8px",
              border: "1px solid var(--border-color)",
            }}
          >
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
        ))}
      </div>
    </div>
  );
}
