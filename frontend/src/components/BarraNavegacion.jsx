import React, { useState } from "react";
import { UploadCloud, RefreshCw, FileText, Sheet, Settings2, Loader2 } from "lucide-react";
import { downloadExportPdf, downloadExportExcel } from "../servicios/api";

export default function BarraNavegacion({ alAbrirCarga, alAbrirGestion, alActualizar, cargando, filtros }) {
  const [exportandoPdf, setExportandoPdf] = useState(false);
  const [exportandoExcel, setExportandoExcel] = useState(false);

  const descargarPdf = async () => {
    try {
      setExportandoPdf(true);
      await downloadExportPdf(filtros);
    } catch (err) {
      alert("Error al descargar PDF: " + err.message);
    } finally {
      setExportandoPdf(false);
    }
  };

  const descargarExcel = async () => {
    try {
      setExportandoExcel(true);
      await downloadExportExcel(filtros);
    } catch (err) {
      alert("Error al descargar Excel: " + err.message);
    } finally {
      setExportandoExcel(false);
    }
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
            disabled={exportandoPdf}
            title="Descargar Informe Ejecutivo en PDF"
          >
            {exportandoPdf ? (
              <Loader2 size={16} className="spin" style={{ color: "#dc2626" }} />
            ) : (
              <FileText size={16} style={{ color: "#dc2626" }} />
            )}
            <span>{exportandoPdf ? "Generando..." : "Reporte PDF"}</span>
          </button>

          <button
            className="btn btn-secondary btn-sm"
            onClick={descargarExcel}
            disabled={exportandoExcel}
            title="Descargar Datos en Planilla Excel"
          >
            {exportandoExcel ? (
              <Loader2 size={16} className="spin" style={{ color: "#16a34a" }} />
            ) : (
              <Sheet size={16} style={{ color: "#16a34a" }} />
            )}
            <span>{exportandoExcel ? "Exportando..." : "Exportar Excel"}</span>
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
