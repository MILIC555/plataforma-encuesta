import React, { useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { Sparkles, MessageSquare, RefreshCw, CheckCircle } from "lucide-react";
import { triggerAiAnalysis } from "../servicios/api";

const COLORES_SENTIMIENTO = {
  positivo: "#10b981", // verde
  neutro: "#94a3b8",   // gris / neutro
  negativo: "#ef4444", // rojo
};

export default function PanelIa({ datosIa, alRecargar }) {
  const [analizando, setAnalizando] = useState(false);
  const [mensaje, setMensaje] = useState(null);

  if (!datosIa) return null;

  const { sentiment = {}, topics = [], summary = "" } = datosIa;

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

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <Sparkles size={20} style={{ color: "#7c3aed" }} />
            <span>Inteligencia Artificial — Análisis de Comentarios (Q09)</span>
          </h3>
          <p className="card-subtitle">
            Clasificación semántica automática de sugerencias y observaciones de alumnos
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
    </div>
  );
}
