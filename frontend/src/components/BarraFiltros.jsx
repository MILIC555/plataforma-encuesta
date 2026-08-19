import React from "react";
import { Filter, Calendar, BookOpen, RotateCcw } from "lucide-react";

export default function BarraFiltros({
  cursos,
  cursoSeleccionado,
  alSeleccionarCurso,
  fechaInicio,
  setFechaInicio,
  fechaFin,
  setFechaFin,
  alLimpiar,
}) {
  return (
    <div className="filter-card">
      <div className="filter-group">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 600, fontSize: "0.9rem", color: "var(--text-main)", marginRight: "0.5rem" }}>
          <Filter size={18} style={{ color: "var(--primary)" }} />
          <span>Filtros de Análisis:</span>
        </div>

        <div className="filter-item">
          <BookOpen size={16} />
          <select
            className="select-input"
            value={cursoSeleccionado || ""}
            onChange={(e) => alSeleccionarCurso(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Todos los cursos ({cursos?.length || 0})</option>
            {cursos?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-item">
          <Calendar size={16} />
          <input
            type="date"
            className="text-input"
            style={{ minWidth: "140px" }}
            value={fechaInicio || ""}
            onChange={(e) => setFechaInicio(e.target.value)}
            placeholder="Desde"
          />
          <span style={{ color: "var(--text-muted)" }}>a</span>
          <input
            type="date"
            className="text-input"
            style={{ minWidth: "140px" }}
            value={fechaFin || ""}
            onChange={(e) => setFechaFin(e.target.value)}
            placeholder="Hasta"
          />
        </div>
      </div>

      {(cursoSeleccionado || fechaInicio || fechaFin) && (
        <button className="btn btn-secondary btn-sm" onClick={alLimpiar}>
          <RotateCcw size={14} />
          <span>Limpiar filtros</span>
        </button>
      )}
    </div>
  );
}
