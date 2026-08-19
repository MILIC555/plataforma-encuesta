import React from "react";
import { UploadCloud, RefreshCw, FileText, Sheet, Settings2 } from "lucide-react";
import { getExportPdfUrl, getExportExcelUrl } from "../servicios/api";

export default function BarraNavegacion({ alAbrirCarga, alAbrirGestion, alActualizar, cargando, filtros }) {
  const descargarPdf = () => {
    const url = getExportPdfUrl(filtros);
    window.open(url, "_blank");
  };

  const descargarExcel = () => {
    const url = getExportExcelUrl(filtros);
    window.open(url, "_blank");
  };

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="brand">
          <div className="brand-badge">CC</div>
          <div>
            <h1 className="brand-title">Campus Córdoba — Analytics</h1>
            <p className="brand-subtitle">Plataforma de Análisis de Encuestas y Satisfacción</p>
          </div>
        </div>

        <div className="navbar-actions">
          <button
            className="btn btn-secondary btn-sm"
            onClick={descargarPdf}
            title="Descargar Informe Ejecutivo en PDF"
          >
            <FileText size={16} style={{ color: "#dc2626" }} />
            <span>Reporte PDF</span>
          </button>

          <button
            className="btn btn-secondary btn-sm"
            onClick={descargarExcel}
            title="Descargar Datos en Planilla Excel"
          >
            <Sheet size={16} style={{ color: "#16a34a" }} />
            <span>Exportar Excel</span>
          </button>

          <button
            className="btn btn-secondary btn-sm"
            onClick={alAbrirGestion}
            title="Gestionar o borrar encuestas y cursos"
          >
            <Settings2 size={16} />
            <span>Gestionar Datos</span>
          </button>

          <button
            className="btn btn-secondary btn-sm"
            onClick={alActualizar}
            disabled={cargando}
            title="Recargar datos"
          >
            <RefreshCw size={14} className={cargando ? "spin" : ""} />
            <span>Actualizar</span>
          </button>

          <button className="btn btn-primary" onClick={alAbrirCarga}>
            <UploadCloud size={18} />
            <span>Cargar Encuestas</span>
          </button>
        </div>
      </div>
    </header>
  );
}
