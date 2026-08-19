import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingUp } from "lucide-react";

export default function GraficoTendencias({ tendencias }) {
  if (!tendencias || tendencias.length === 0) return null;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <TrendingUp size={20} style={{ color: "var(--primary)" }} />
            <span>Evolución Temporal de Calificaciones</span>
          </h3>
          <p className="card-subtitle">
            Tendencia del promedio general mes a mes
          </p>
        </div>
      </div>

      <div style={{ height: "220px", width: "100%" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={tendencias} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="period" tick={{ fontSize: 12, fill: "#64748b" }} />
            <YAxis domain={[0, 10]} ticks={[0, 2, 4, 6, 8, 10]} tick={{ fontSize: 12, fill: "#64748b" }} />
            <Tooltip
              formatter={(value) => [`${value} / 10`, "Calificación Promedio"]}
              labelFormatter={(label) => `Período: ${label}`}
            />
            <Line
              type="monotone"
              dataKey="average_score"
              stroke="#2563eb"
              strokeWidth={3}
              dot={{ r: 5, fill: "#2563eb" }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
