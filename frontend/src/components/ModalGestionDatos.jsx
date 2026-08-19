import React, { useState } from "react";
import { X, Trash2, AlertTriangle, CheckCircle2, RefreshCw, BookOpen } from "lucide-react";
import { deleteCourse, clearAllSurveys } from "../servicios/api";

export default function ModalGestionDatos({ estaAbierto, alCerrar, cursos, alActualizarDatos }) {
  const [cargando, setCargando] = useState(false);
  const [mensajeExito, setMensajeExito] = useState(null);
  const [error, setError] = useState(null);
  const [confirmandoVaciar, setConfirmandoVaciar] = useState(false);
  const [cursoAEliminar, setCursoAEliminar] = useState(null);

  if (!estaAbierto) return null;

  const manejarEliminarCurso = async (curso) => {
    setCargando(true);
    setError(null);
    setMensajeExito(null);

    try {
      const res = await deleteCourse(curso.id);
      setMensajeExito(res.message || `Curso '${curso.name}' eliminado correctamente.`);
      setCursoAEliminar(null);
      if (alActualizarDatos) alActualizarDatos();
    } catch (err) {
      setError(err.message || "Error al eliminar el curso.");
    } finally {
      setCargando(false);
    }
  };

  const manejarVaciarTodo = async () => {
    setCargando(true);
    setError(null);
    setMensajeExito(null);

    try {
      const res = await clearAllSurveys();
      setMensajeExito(res.message || "Se eliminaron todas las encuestas cargadas.");
      setConfirmandoVaciar(false);
      if (alActualizarDatos) alActualizarDatos();
    } catch (err) {
      setError(err.message || "Error al vaciar los datos.");
    } finally {
      setCargando(false);
    }
  };

  const cerrarModal = () => {
    setMensajeExito(null);
    setError(null);
    setConfirmandoVaciar(false);
    setCursoAEliminar(null);
    alCerrar();
  };

  return (
    <div className="modal-backdrop" onClick={cerrarModal}>
      <div className="modal-card" style={{ maxWidth: "600px" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
          <div>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-main)" }}>
              Gestión y Eliminación de Datos
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
              Eliminá encuestas de cursos específicos o vaciá la base de datos para comenzar de nuevo.
            </p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={cerrarModal} style={{ borderRadius: "50%", padding: "0.4rem" }}>
            <X size={18} />
          </button>
        </div>

        {mensajeExito && (
          <div style={{ padding: "0.6rem 0.85rem", background: "var(--success-bg)", color: "var(--success)", borderRadius: "6px", fontSize: "0.85rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <CheckCircle2 size={16} />
            <span>{mensajeExito}</span>
          </div>
        )}

        {error && (
          <div style={{ padding: "0.6rem 0.85rem", background: "var(--danger-bg)", color: "var(--danger)", borderRadius: "6px", fontSize: "0.85rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Modal de confirmación para eliminar un curso */}
        {cursoAEliminar && (
          <div style={{ padding: "1rem", background: "#fff1f2", border: "1px solid #fecdd3", borderRadius: "8px", marginBottom: "1rem" }}>
            <p style={{ fontWeight: 700, color: "#9f1239", fontSize: "0.9rem", marginBottom: "0.35rem" }}>
              ¿Confirmás la eliminación del curso?
            </p>
            <p style={{ fontSize: "0.85rem", color: "#881337", marginBottom: "0.85rem" }}>
              Se borrarán permanentemente el curso <strong>"{cursoAEliminar.name}"</strong> y todas sus <strong>{cursoAEliminar.total_surveys}</strong> encuestas asociadas.
            </p>
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setCursoAEliminar(null)} disabled={cargando}>
                Cancelar
              </button>
              <button className="btn btn-sm" style={{ backgroundColor: "var(--danger)", color: "white" }} onClick={() => manejarEliminarCurso(cursoAEliminar)} disabled={cargando}>
                {cargando ? "Eliminando..." : "Sí, Eliminar Curso"}
              </button>
            </div>
          </div>
        )}

        {/* Modal de confirmación para vaciar TODO */}
        {confirmandoVaciar && (
          <div style={{ padding: "1rem", background: "#fff1f2", border: "1px solid #fecdd3", borderRadius: "8px", marginBottom: "1rem" }}>
            <p style={{ fontWeight: 700, color: "#9f1239", fontSize: "0.9rem", marginBottom: "0.35rem" }}>
              ⚠️ ¡ADVERTENCIA! Vaciar todos los datos
            </p>
            <p style={{ fontSize: "0.85rem", color: "#881337", marginBottom: "0.85rem" }}>
              Esta acción borrará <strong>todas las encuestas, respuestas y cursos</strong> de la base de datos. Los análisis quedarán en cero.
            </p>
            <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setConfirmandoVaciar(false)} disabled={cargando}>
                Cancelar
              </button>
              <button className="btn btn-sm" style={{ backgroundColor: "var(--danger)", color: "white" }} onClick={manejarVaciarTodo} disabled={cargando}>
                {cargando ? "Vaciando..." : "Sí, Vaciar Todo"}
              </button>
            </div>
          </div>
        )}

        {/* Lista de cursos activos */}
        <div style={{ marginBottom: "1.5rem" }}>
          <h4 style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.6rem" }}>
            Cursos y Encuestas Cargadas ({cursos?.length || 0}):
          </h4>

          <div style={{ maxHeight: "220px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {cursos && cursos.length > 0 ? (
              cursos.map((c) => (
                <div
                  key={c.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.6rem 0.85rem",
                    background: "var(--bg-main)",
                    borderRadius: "6px",
                    border: "1px solid var(--border-color)",
                    fontSize: "0.85rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <BookOpen size={16} style={{ color: "var(--primary)", flexShrink: 0 }} />
                    <div>
                      <div style={{ fontWeight: 600, color: "var(--text-main)" }}>{c.name}</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {c.total_surveys !== undefined ? `${c.total_surveys} encuestas` : "Curso activo"}
                      </div>
                    </div>
                  </div>

                  <button
                    className="btn btn-secondary btn-sm"
                    style={{ color: "var(--danger)", padding: "0.3rem 0.6rem" }}
                    onClick={() => setCursoAEliminar(c)}
                    title="Eliminar este curso y sus encuestas"
                    disabled={cargando}
                  >
                    <Trash2 size={14} />
                    <span>Eliminar</span>
                  </button>
                </div>
              ))
            ) : (
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", textAlign: "center", padding: "1.5rem 0" }}>
                No hay cursos ni encuestas registradas actualmente.
              </p>
            )}
          </div>
        </div>

        {/* Acciones inferiores */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--border-color)", paddingTop: "1rem" }}>
          {cursos && cursos.length > 0 ? (
            <button
              className="btn btn-secondary btn-sm"
              style={{ color: "var(--danger)", borderColor: "#fecdd3" }}
              onClick={() => setConfirmandoVaciar(true)}
              disabled={cargando}
            >
              <Trash2 size={14} />
              <span>Vaciar Toda la Base</span>
            </button>
          ) : <div />}

          <button className="btn btn-primary btn-sm" onClick={cerrarModal}>
            Listo / Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}
