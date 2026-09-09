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
    <div className="filter-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
      <div className="filter-group">
        <div className="filter-item">
          <BookOpen size={16} style={{ color: "var(--primary)" }} />
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
          <Calendar size={16} style={{ color: "var(--primary)" }} />
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
