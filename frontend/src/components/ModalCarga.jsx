import React, { useState, useRef } from "react";
import { X, UploadCloud, CheckCircle2, AlertCircle, FileSpreadsheet, Trash2 } from "lucide-react";
import { uploadSurveyFiles } from "../servicios/api";

export default function ModalCarga({ estaAbierto, alCerrar, alCompletarCarga }) {
  const [archivos, setArchivos] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [arrastrando, setArrastrando] = useState(false);
  const inputRef = useRef(null);

  if (!estaAbierto) return null;

  const agregarArchivos = (nuevosArchivos) => {
    const validos = Array.from(nuevosArchivos).filter((f) => {
      const ext = f.name.toLowerCase();
      return ext.endsWith(".csv") || ext.endsWith(".xlsx") || ext.endsWith(".xls");
    });

    if (validos.length === 0) {
      setError("Por favor seleccioná archivos con extensión .csv, .xlsx o .xls");
      return;
    }

    setError(null);
    setResultado(null);
    setArchivos((prev) => {
      const nombresExistentes = new Set(prev.map((a) => a.name));
      const noDuplicados = validos.filter((f) => !nombresExistentes.has(f.name));
      return [...prev, ...noDuplicados];
    });
  };

  const manejarArrastre = (e) => {
    e.preventDefault();
    setArrastrando(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      agregarArchivos(e.dataTransfer.files);
    }
  };

  const manejarSeleccion = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      agregarArchivos(e.target.files);
    }
  };

  const eliminarArchivo = (nombre) => {
    setArchivos((prev) => prev.filter((a) => a.name !== nombre));
  };

  const manejarSubida = async () => {
    if (archivos.length === 0) return;
    setCargando(true);
    setError(null);
    setResultado(null);

    try {
      const res = await uploadSurveyFiles(archivos);
      setResultado(res);
      if (alCompletarCarga) alCompletarCarga();
    } catch (err) {
      setError(err.message || "Error al procesar los archivos");
    } finally {
      setCargando(false);
    }
  };

  const cerrarModal = () => {
    setArchivos([]);
    setResultado(null);
    setError(null);
    alCerrar();
  };

  return (
    <div className="modal-backdrop" onClick={cerrarModal}>
      <div className="modal-card" style={{ maxWidth: "640px" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
          <div>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-main)" }}>
              Carga de Encuestas (Individual o Masiva)
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
              Podés subir 1 o varios archivos (.csv / .xlsx) simultáneamente. Las encuestas duplicadas se ignorarán automáticamente.
            </p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={cerrarModal} style={{ borderRadius: "50%", padding: "0.4rem" }}>
            <X size={18} />
          </button>
        </div>

        {!resultado ? (
          <>
            <div
              className={`dropzone ${arrastrando ? "active" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setArrastrando(true); }}
              onDragLeave={() => setArrastrando(false)}
              onDrop={manejarArrastre}
              onClick={() => inputRef.current?.click()}
            >
              <input
                type="file"
                ref={inputRef}
                style={{ display: "none" }}
                multiple
                accept=".csv, .xlsx, .xls"
                onChange={manejarSeleccion}
              />
              <UploadCloud size={44} style={{ color: "var(--primary)", margin: "0 auto 0.75rem auto" }} />
              <div>
                <p style={{ fontWeight: 600, color: "var(--text-main)" }}>
                  Arrastrá uno o varios archivos acá o hacé clic para explorar
                </p>
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                  Archivos CSV exportados por curso o planillas Excel (.xlsx / .xls)
                </p>
              </div>
            </div>

            {/* Lista de archivos seleccionados */}
            {archivos.length > 0 && (
              <div style={{ marginTop: "1rem", maxHeight: "180px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600 }}>
                  <span>Archivos a procesar ({archivos.length}):</span>
                  <span style={{ cursor: "pointer", color: "var(--danger)" }} onClick={() => setArchivos([])}>Limpiar todo</span>
                </div>
                {archivos.map((arch) => (
                  <div
                    key={arch.name}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "0.5rem 0.75rem",
                      background: "var(--bg-main)",
                      borderRadius: "6px",
                      border: "1px solid var(--border-color)",
                      fontSize: "0.85rem",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", overflow: "hidden" }}>
                      <FileSpreadsheet size={16} style={{ color: "var(--primary)", flexShrink: 0 }} />
                      <span style={{ fontWeight: 600, color: "var(--text-main)", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                        {arch.name}
                      </span>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", flexShrink: 0 }}>
                        ({(arch.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                    <button
                      className="btn btn-secondary btn-sm"
                      style={{ padding: "0.2rem 0.4rem", border: "none", color: "var(--danger)" }}
                      onClick={(e) => { e.stopPropagation(); eliminarArchivo(arch.name); }}
                      title="Quitar de la lista"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {error && (
              <div style={{ marginTop: "1rem", padding: "0.75rem 1rem", backgroundColor: "var(--danger-bg)", color: "var(--danger)", borderRadius: "8px", display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.875rem" }}>
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.5rem" }}>
              <button className="btn btn-secondary" onClick={cerrarModal} disabled={cargando}>
                Cancelar
              </button>
              <button className="btn btn-primary" onClick={manejarSubida} disabled={archivos.length === 0 || cargando}>
                {cargando
                  ? `Procesando ${archivos.length} archivo(s)...`
                  : archivos.length > 1
                  ? `Procesar ${archivos.length} Archivos Masivamente`
                  : "Subir e Importar"}
              </button>
            </div>
          </>
        ) : (
          <div style={{ textAlign: "center", padding: "1rem 0" }}>
            <CheckCircle2 size={52} style={{ color: "var(--success)", margin: "0 auto 1rem auto" }} />
            <h4 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.5rem" }}>
              ¡Procesamiento Completado!
            </h4>
            <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
              {resultado.message}
            </p>

            <div style={{ background: "var(--bg-main)", borderRadius: "8px", padding: "1rem", textAlign: "left", fontSize: "0.875rem", marginBottom: "1.5rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.35rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Archivos procesados:</span>
                <strong>{resultado.total_files}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.35rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Total filas evaluadas:</span>
                <strong>{resultado.total_rows}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.35rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Nuevas encuestas importadas:</span>
                <strong style={{ color: "var(--success)" }}>+{resultado.imported_surveys}</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.35rem" }}>
                <span style={{ color: "var(--text-muted)" }}>Encuestas duplicadas ignoradas:</span>
                <strong style={{ color: "var(--warning)" }}>{resultado.skipped_duplicates}</strong>
              </div>
              {resultado.courses_affected?.length > 0 && (
                <div style={{ marginTop: "0.5rem", borderTop: "1px solid var(--border-color)", paddingTop: "0.5rem" }}>
                  <span style={{ color: "var(--text-muted)" }}>Cursos actualizados:</span>
                  <p style={{ fontWeight: 600, marginTop: "0.2rem" }}>{resultado.courses_affected.join(", ")}</p>
                </div>
              )}
            </div>

            <button className="btn btn-primary" style={{ width: "100%" }} onClick={cerrarModal}>
              Cerrar y Ver Resultados
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
