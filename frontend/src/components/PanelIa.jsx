import React, { useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { Sparkles, MessageSquare, RefreshCw, CheckCircle, AlertTriangle, ArrowDownRight, ShieldAlert } from "lucide-react";
import { triggerAiAnalysis } from "../servicios/api";

const COLORES_SENTIMIENTO = {
  positivo: "#10b981", // verde
  neutro: "#94a3b8",   // gris / neutro
  negativo: "#ef4444", // rojo
};

export default function PanelIa({ datosIa, alRecargar, alFiltrarNegativos }) {
  const [analizando, setAnalizando] = useState(false);
  const [mensaje, setMensaje] = useState(null);

  if (!datosIa) return null;

  const { sentiment = {}, topics = [], summary = "", negative_insights = {} } = datosIa;

  const datosSentimiento = [
    { name: "Positivo", value: sentiment.positivo || 0, color: COLORES_SENTIMIENTO.positivo },
    { name: "Neutro / Sin objeción", value: sentiment.neutro || 0, color: COLORES_SENTIMIENTO.neutro },
    { name: "Negativo / Reclamo", value: sentiment.negativo || 0, color: COLORES_SENTIMIENTO.negativo },
  ].filter((d) => d.value > 0);

  const ejecutarAnalisisIa = async () => {
    setAnalizando(true);
    setMensaje(null);
    try {
      const res = await triggerAiAnalysis();
      setMensaje(res.message || "Análisis completado");
      if (alRecargar) alRecargar();
    } catch (err) {
      setMensaje("Error ejecutando análisis de IA");
    } finally {
      setAnalizando(false);
    }
  };

  const negativosPorTema = negative_insights.by_topic || [];
  const totalNegativos = negative_insights.total_negatives || sentiment.negativo || 0;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <Sparkles size={20} style={{ color: "#7c3aed" }} />
            <span>Inteligencia Artificial — Análisis de Comentarios (Q09)</span>
          </h3>
          <p className="card-subtitle">
            Procesamiento semántico con Hugging Face para detección de sentimiento y focos de mejora
          </p>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={ejecutarAnalisisIa} disabled={analizando}>
          <RefreshCw size={14} className={analizando ? "spin" : ""} />
          <span>{analizando ? "Analizando..." : "Re-analizar con IA"}</span>
        </button>
      </div>

      {mensaje && (
        <div style={{ padding: "0.5rem 0.85rem", background: "#f0fdf4", color: "#166534", borderRadius: "6px", fontSize: "0.8rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
          <CheckCircle size={14} />
          <span>{mensaje}</span>
        </div>
      )}

      {/* Resumen Ejecutivo IA */}
      <div style={{ background: "linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%)", borderRadius: "10px", padding: "1.1rem 1.25rem", border: "1px solid #ddd6fe", marginBottom: "1.25rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
          <Sparkles size={16} style={{ color: "#6d28d9" }} />
          <strong style={{ fontSize: "0.85rem", color: "#5b21b6", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Resumen Ejecutivo Generado por IA
          </strong>
        </div>
        <p style={{ fontSize: "0.9rem", color: "#3730a3", lineHeight: 1.6 }}>
          {summary || "No hay comentarios suficientes para procesar."}
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.25rem" }}>
        {/* Distribución de Sentimiento */}
        <div style={{ background: "var(--bg-main)", borderRadius: "8px", padding: "1rem", border: "1px solid var(--border-color)" }}>
          <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <MessageSquare size={16} style={{ color: "var(--primary)" }} />
            <span>Sentimiento de las Respuestas</span>
          </h4>

          <div style={{ height: "180px", width: "100%" }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={datosSentimiento} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={4} dataKey="value">
                  {datosSentimiento.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div style={{ display: "flex", justifyContent: "center", gap: "1rem", fontSize: "0.75rem", marginTop: "0.5rem" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <span style={{ width: 10, height: 10, borderRadius: "50%", background: COLORES_SENTIMIENTO.positivo }}></span>
              Positivo ({sentiment.positivo || 0})
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <span style={{ width: 10, height: 10, borderRadius: "50%", background: COLORES_SENTIMIENTO.neutro }}></span>
              Neutro ({sentiment.neutro || 0})
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <span style={{ width: 10, height: 10, borderRadius: "50%", background: COLORES_SENTIMIENTO.negativo }}></span>
              Negativo ({sentiment.negativo || 0})
            </span>
          </div>
        </div>

        {/* Tópicos Principales */}
        <div style={{ background: "var(--bg-main)", borderRadius: "8px", padding: "1rem", border: "1px solid var(--border-color)" }}>
          <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.75rem" }}>
            Temáticas Más Mencionadas
          </h4>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {topics.length > 0 ? (
              topics.map((t) => (
                <div key={t.topic} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: "0.85rem", color: "var(--text-main)" }}>{t.label}</span>
                  <span className="badge badge-topic">{t.count} menciones</span>
                </div>
              ))
            ) : (
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Sin tópicos clasificados aún.</p>
            )}
          </div>
        </div>
      </div>

      {/* Módulo Especial: Diagnóstico de Respuestas Negativas y Reclamos */}
      <div
        style={{
          marginTop: "1.25rem",
          background: totalNegativos > 0 ? "#fef2f2" : "var(--bg-main)",
          border: totalNegativos > 0 ? "1px solid #fecaca" : "1px solid var(--border-color)",
          borderRadius: "10px",
          padding: "1.1rem 1.25rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem", flexWrap: "wrap", gap: "0.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <ShieldAlert size={18} style={{ color: totalNegativos > 0 ? "var(--danger)" : "var(--text-muted)" }} />
            <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: totalNegativos > 0 ? "#991b1b" : "var(--text-main)" }}>
              Focos de Mejora y Reclamos Críticos ({totalNegativos} detectados)
            </h4>
          </div>

          {alFiltrarNegativos && (
            <button
              className="btn btn-secondary btn-sm"
              style={{ fontSize: "0.75rem", borderColor: totalNegativos > 0 ? "#fca5a5" : "var(--border-color)", color: totalNegativos > 0 ? "var(--danger)" : "var(--text-main)" }}
              onClick={alFiltrarNegativos}
            >
              <ArrowDownRight size={14} />
              <span>Ver Comentarios Negativos en el Muro</span>
            </button>
          )}
        </div>

        {totalNegativos > 0 ? (
          <div>
            <p style={{ fontSize: "0.825rem", color: "#7f1d1d", marginBottom: "0.75rem" }}>
              Distribución de opiniones críticas clasificadas por área para priorizar acciones correctivas:
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "0.6rem" }}>
              {negativosPorTema.map((negItem) => (
                <div
                  key={negItem.topic}
                  style={{
                    background: "white",
                    padding: "0.5rem 0.75rem",
                    borderRadius: "6px",
                    border: "1px solid #fecaca",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "#450a0a" }}>
                    {negItem.label}
                  </span>
                  <span className="badge badge-danger" style={{ fontSize: "0.75rem" }}>
                    {negItem.count} {negItem.count === 1 ? "queja" : "quejas"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            No se han registrado comentarios negativos significativos en este segmento de encuestas.
          </p>
        )}
      </div>
    </div>
  );
}
