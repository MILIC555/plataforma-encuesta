import React, { useState, useRef, useEffect } from "react";
import { X, UploadCloud, CheckCircle2, AlertCircle, FileSpreadsheet, FileText, Trash2, Loader2, ArrowRight, PlusCircle, FolderPlus, Files } from "lucide-react";
import { uploadSurveyFiles } from "../servicios/api";

export default function ModalCarga({ estaAbierto, alCerrar, alCompletarCarga }) {
  const [archivos, setArchivos] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [arrastrando, setArrastrando] = useState(false);

  const inputFileRef = useRef(null);
  const inputFolderRef = useRef(null);

  // Escuchar tecla ESC para cerrar
  useEffect(() => {
    const alPresionarTecla = (e) => {
      if (e.key === "Escape" && estaAbierto) {
        cerrarModal();
      }
    };
    window.addEventListener("keydown", alPresionarTecla);
    return () => window.removeEventListener("keydown", alPresionarTecla);
  }, [estaAbierto]);

  if (!estaAbierto) return null;

  const esExtensionValida = (nombre) => {
    const min = nombre.toLowerCase();
    return min.endsWith(".csv") || min.endsWith(".xlsx") || min.endsWith(".xls") || min.endsWith(".pdf");
  };

  const agregarArchivos = (nuevosArchivos) => {
    const validos = Array.from(nuevosArchivos).filter((f) => esExtensionValida(f.name));

    if (validos.length === 0) {
      setError("Por favor seleccioná o arrastrá archivos válidos (.csv, .xlsx, .xls o .pdf)");
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

  // Travesía recursiva para carpetas soltadas por Drag & Drop
  const recorrerEntrada = async (entry, listaSalida) => {
    if (entry.isFile) {
      return new Promise((resolve) => {
        entry.file((file) => {
          if (esExtensionValida(file.name)) {
            listaSalida.push(file);
          }
          resolve();
        });
      });
    } else if (entry.isDirectory) {
      const dirReader = entry.createReader();
      const leerEntradas = () =>
        new Promise((resolve) => {
          dirReader.readEntries(async (entries) => {
            if (!entries || entries.length === 0) {
              resolve();
            } else {
              for (const childEntry of entries) {
                await recorrerEntrada(childEntry, listaSalida);
              }
              resolve();
            }
          });
        });
      await leerEntradas();
    }
  };

  const manejarArrastre = async (e) => {
    e.preventDefault();
    setArrastrando(false);

    const items = e.dataTransfer.items;
    const listaArchivos = [];

    if (items && items.length > 0 && items[0].webkitGetAsEntry) {
      for (let i = 0; i < items.length; i++) {
        const entry = items[i].webkitGetAsEntry();
        if (entry) {
          await recorrerEntrada(entry, listaArchivos);
        }
      }
      if (listaArchivos.length > 0) {
        agregarArchivos(listaArchivos);
        return;
      }
    }

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      agregarArchivos(e.dataTransfer.files);
    }
  };

  const manejarSeleccionArchivos = (e) => {
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

  const reiniciarParaMasCargas = () => {
    setArchivos([]);
    setResultado(null);
    setError(null);
  };

  const cerrarModal = () => {
    setArchivos([]);
    setResultado(null);
    setError(null);
    alCerrar();
  };

  return (
    <div className="modal-backdrop" onClick={cerrarModal}>
      <div
        className="modal-card"
        style={{
          maxWidth: "680px",
          maxHeight: "92vh",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera del modal */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.25rem" }}>
          <div>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-main)" }}>
              {resultado ? "¡Carga Completada con Éxito!" : "Carga de Encuestas (Archivos o Carpetas)"}
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
              {resultado
                ? "Los datos se procesaron e ingresaron al sistema inmediatamente."
                : "Podés seleccionar o arrastrar carpetas completas o archivos sueltos (.csv, .xlsx, .pdf)."}
            </p>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={cerrarModal}
            style={{ borderRadius: "50%", padding: "0.45rem", marginLeft: "0.5rem" }}
            title="Cerrar ventana"
          >
            <X size={18} />
          </button>
        </div>

        {!resultado ? (
          <>
            {/* Inputs ocultos */}
            <input
              type="file"
              ref={inputFileRef}
              style={{ display: "none" }}
              multiple
              accept=".csv, .xlsx, .xls, .pdf"
              onChange={manejarSeleccionArchivos}
            />
            <input
              type="file"
              ref={inputFolderRef}
              style={{ display: "none" }}
              webkitdirectory=""
              directory=""
              multiple
              onChange={manejarSeleccionArchivos}
            />

            {/* Zona de Dropzone */}
            <div
              className={`dropzone ${arrastrando ? "active" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setArrastrando(true); }}
              onDragLeave={() => setArrastrando(false)}
              onDrop={manejarArrastre}
              style={{ padding: "1.75rem 1rem", border: "2px dashed var(--border-color)", borderRadius: "12px", textAlign: "center", background: arrastrando ? "var(--primary-light)" : "var(--bg-main)" }}
            >
              <UploadCloud size={44} style={{ color: "var(--primary)", margin: "0 auto 0.75rem auto" }} />
              <p style={{ fontWeight: 700, color: "var(--text-main)", fontSize: "0.95rem" }}>
                Arrastrá una carpeta entera o varios archivos acá
              </p>
              <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem", marginBottom: "1.25rem" }}>
                Formatos soportados: CSV, Excel (.xlsx) y PDF de Moodle
              </p>

              {/* Botones duales: Cargar Carpeta vs Cargar Archivos */}
              <div style={{ display: "flex", justifyContent: "center", gap: "0.75rem", flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={(e) => { e.stopPropagation(); inputFolderRef.current?.click(); }}
                >
                  <FolderPlus size={16} />
                  <span>Cargar Carpeta Completa</span>
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={(e) => { e.stopPropagation(); inputFileRef.current?.click(); }}
                >
                  <Files size={16} />
                  <span>Seleccionar Archivos</span>
                </button>
              </div>
            </div>

            {/* Indicador de progreso de subida */}
            {cargando && (
              <div style={{ marginTop: "1rem", padding: "1rem", background: "linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)", borderRadius: "8px", border: "1px solid #bfdbfe", display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <Loader2 size={24} className="spin" style={{ color: "var(--primary)" }} />
                <div>
                  <p style={{ fontWeight: 700, color: "#1e3a8a", fontSize: "0.9rem" }}>
                    Procesando e importando {archivos.length} archivo(s)...
                  </p>
                  <p style={{ fontSize: "0.75rem", color: "#3b82f6" }}>
                    Normalizando encuestas y registrando en la base de datos de forma ultra veloz
                  </p>
                </div>
              </div>
            )}

            {/* Lista de archivos seleccionados */}
            {archivos.length > 0 && !cargando && (
              <div style={{ marginTop: "1rem", maxHeight: "200px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: 600 }}>
                  <span>Archivos detectados en la selección ({archivos.length}):</span>
                  <span style={{ cursor: "pointer", color: "var(--danger)" }} onClick={() => setArchivos([])}>Limpiar lista</span>
                </div>
                {archivos.map((arch, idx) => {
                  const esPdf = arch.name.toLowerCase().endsWith(".pdf");
                  return (
                    <div
                      key={`${arch.name}-${idx}`}
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
                        {esPdf ? (
                          <FileText size={16} style={{ color: "var(--danger)", flexShrink: 0 }} />
                        ) : (
                          <FileSpreadsheet size={16} style={{ color: "var(--primary)", flexShrink: 0 }} />
                        )}
                        <span style={{ fontWeight: 600, color: "var(--text-main)", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                          {arch.name}
                        </span>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", flexShrink: 0 }}>
                          ({(arch.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        style={{ padding: "0.2rem 0.4rem", border: "none", color: "var(--danger)" }}
                        onClick={(e) => { e.stopPropagation(); eliminarArchivo(arch.name); }}
                        title="Quitar de la lista"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}

            {error && (
              <div style={{ marginTop: "1rem", padding: "0.75rem 1rem", backgroundColor: "var(--danger-bg)", color: "var(--danger)", borderRadius: "8px", display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.875rem" }}>
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.5rem" }}>
              <button type="button" className="btn btn-secondary" onClick={cerrarModal} disabled={cargando}>
                Cancelar
              </button>
              <button type="button" className="btn btn-primary" onClick={manejarSubida} disabled={archivos.length === 0 || cargando}>
                {cargando
                  ? `Importando ${archivos.length} archivo(s)...`
                  : archivos.length > 1
                    ? `Procesar Carpeta / ${archivos.length} Archivos`
                    : "Subir e Importar"}
              </button>
            </div>
          </>
        ) : (
          /* Pantalla de Éxito / Resumen */
          <div style={{ padding: "0.5rem 0" }}>
            <div style={{ textAlign: "center", marginBottom: "1.25rem" }}>
              <CheckCircle2 size={48} style={{ color: "var(--success)", margin: "0 auto 0.5rem auto" }} />
              <h4 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)" }}>
                {resultado.imported_surveys > 0
                  ? `¡Se importaron ${resultado.imported_surveys} encuestas nuevas!`
                  : "Proceso completado sin encuestas nuevas que agregar"}
              </h4>
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                {resultado.message}
              </p>
            </div>

            {/* Tarjeta de métricas del lote */}
            <div style={{ background: "var(--bg-main)", borderRadius: "8px", padding: "1rem", border: "1px solid var(--border-color)", marginBottom: "1.25rem", fontSize: "0.875rem" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
                <div style={{ background: "white", padding: "0.6rem 0.8rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Archivos Leídos</span>
                  <strong style={{ fontSize: "1.1rem", color: "var(--text-main)" }}>{resultado.total_files}</strong>
                </div>
                <div style={{ background: "white", padding: "0.6rem 0.8rem", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block" }}>Registros Evaluados</span>
                  <strong style={{ fontSize: "1.1rem", color: "var(--text-main)" }}>{resultado.total_rows}</strong>
                </div>
                <div style={{ background: "var(--success-bg)", padding: "0.6rem 0.8rem", borderRadius: "6px", border: "1px solid #bbf7d0" }}>
                  <span style={{ fontSize: "0.75rem", color: "#166534", display: "block" }}>Encuestas Nuevas</span>
                  <strong style={{ fontSize: "1.1rem", color: "var(--success)" }}>+{resultado.imported_surveys}</strong>
                </div>
                <div style={{ background: "var(--warning-bg)", padding: "0.6rem 0.8rem", borderRadius: "6px", border: "1px solid #fde68a" }}>
                  <span style={{ fontSize: "0.75rem", color: "#92400e", display: "block" }}>Duplicadas Omitidas</span>
                  <strong style={{ fontSize: "1.1rem", color: "var(--warning)" }}>{resultado.skipped_duplicates}</strong>
                </div>
              </div>

              {/* Lista compacta de cursos impactados */}
              {resultado.courses_affected?.length > 0 && (
                <div style={{ borderTop: "1px solid var(--border-color)", paddingTop: "0.6rem" }}>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600, display: "block", marginBottom: "0.4rem" }}>
                    Cursos actualizados ({resultado.courses_affected.length}):
                  </span>
                  <div style={{ maxHeight: "90px", overflowY: "auto", display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
                    {resultado.courses_affected.map((cName, idx) => (
                      <span key={idx} className="badge badge-neutral" style={{ fontSize: "0.75rem" }}>
                        {cName}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Botones de acción */}
            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ flex: 1, justifyContent: "center" }}
                onClick={reiniciarParaMasCargas}
              >
                <PlusCircle size={16} />
                <span>Cargar Otra Carpeta / Archivo</span>
              </button>

              <button
                type="button"
                className="btn btn-primary"
                style={{ flex: 1.5, justifyContent: "center", padding: "0.75rem 1.25rem", fontSize: "0.95rem" }}
                onClick={cerrarModal}
              >
                <span>Ver Resultados en el Tablero</span>
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
