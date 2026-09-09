import React, { useState, useEffect } from "react";
import { MessageSquare, Search, AlertCircle, ThumbsUp, Info, ShieldAlert, BookOpen } from "lucide-react";
import { fetchComments } from "../servicios/api";

export default function ExploradorComentarios({
  cursos = [],
  cursoSeleccionado,
  filtroSentimientoExterno,
}) {
  const [comentarios, setComentarios] = useState([]);
  const [total, setTotal] = useState(0);
  const [cursoFiltro, setCursoFiltro] = useState(cursoSeleccionado || "");
  const [tema, setTema] = useState("todos");
  const [sentimiento, setSentimiento] = useState("todos");
  const [busqueda, setBusqueda] = useState("");

  // Sincronizar si cambia el curso seleccionado desde la barra global superior
  useEffect(() => {
    setCursoFiltro(cursoSeleccionado || "");
  }, [cursoSeleccionado]);

  // Sincronizar si viene un filtro externo (ej: clic desde el Panel IA)
  useEffect(() => {
    if (filtroSentimientoExterno) {
      setSentimiento(filtroSentimientoExterno);
    }
  }, [filtroSentimientoExterno]);

  const cargarComentarios = async () => {
    try {
      const data = await fetchComments({
        course_id: cursoFiltro ? Number(cursoFiltro) : undefined,
        topic: tema,
        sentiment: sentimiento,
        search: busqueda,
        page_size: 100,
      });
      setComentarios(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error("Error cargando comentarios:", err);
    }
  };

  useEffect(() => {
    cargarComentarios();
  }, [cursoFiltro, tema, sentimiento]);

  const manejarEnvioBusqueda = (e) => {
    e.preventDefault();
    cargarComentarios();
  };

  const obtenerBadgeSentimiento = (sent) => {
    if (sent === "positivo") return <span className="badge badge-success">Positivo</span>;
    if (sent === "negativo") return <span className="badge badge-danger">Crítica / Reclamo</span>;
    return <span className="badge badge-neutral">Neutro</span>;
  };

  return (
    <div className="card" id="muro-comentarios">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <MessageSquare size={20} style={{ color: "var(--primary)" }} />
            <span>Muro de Opiniones y Observaciones Abiertas ({total})</span>
          </h3>
          <p className="card-subtitle">
            Respuestas textuales abiertas analizadas con Inteligencia Artificial por sentimiento y temática
          </p>
        </div>

        {/* Accesos rápidos por sentimiento */}
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
          <button
            className={`btn btn-sm ${sentimiento === "todos" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setSentimiento("todos")}
          >
            Todos
          </button>
          <button
            className={`btn btn-sm ${sentimiento === "negativo" ? "btn-primary" : "btn-secondary"}`}
            style={sentimiento === "negativo" ? { backgroundColor: "var(--danger)", borderColor: "var(--danger)" } : { color: "var(--danger)" }}
            onClick={() => setSentimiento("negativo")}
          >
            <ShieldAlert size={13} />
            <span>Críticas y Reclamos</span>
          </button>
          <button
            className={`btn btn-sm ${sentimiento === "positivo" ? "btn-primary" : "btn-secondary"}`}
            style={sentimiento === "positivo" ? { backgroundColor: "var(--success)", borderColor: "var(--success)" } : { color: "var(--success)" }}
            onClick={() => setSentimiento("positivo")}
          >
            <ThumbsUp size={13} />
            <span>Positivos</span>
          </button>
          <button
            className={`btn btn-sm ${sentimiento === "neutro" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setSentimiento("neutro")}
          >
            <Info size={13} />
            <span>Neutros</span>
          </button>
        </div>
      </div>

      {/* Filtros: Curso, Sentimiento, Tópico y Búsqueda */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1.25rem", background: "var(--bg-main)", padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)", alignItems: "center" }}>
        
        {/* Selector de Curso directo en el Muro */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", minWidth: "220px", flex: 1 }}>
          <BookOpen size={16} style={{ color: "var(--primary)", flexShrink: 0 }} />
          <select
            className="select-input"
            style={{ width: "100%" }}
            value={cursoFiltro || ""}
            onChange={(e) => setCursoFiltro(e.target.value)}
          >
            <option value="">Todos los cursos ({cursos?.length || 0})</option>
            {cursos?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Selector de Sentimiento */}
        <select className="select-input" style={{ minWidth: "160px" }} value={sentimiento} onChange={(e) => setSentimiento(e.target.value)}>
          <option value="todos">Todos los sentimientos</option>
          <option value="negativo">⚠️ Solo Negativos / Reclamos</option>
          <option value="positivo">⭐ Solo Positivos</option>
          <option value="neutro">ℹ️ Solo Neutros</option>
        </select>

        {/* Selector de Temática */}
        <select className="select-input" style={{ minWidth: "180px" }} value={tema} onChange={(e) => setTema(e.target.value)}>
          <option value="todos">Todas las temáticas</option>
          <option value="tutor_docente">Tutoría y Docencia</option>
          <option value="contenidos_material">Contenidos y Material</option>
          <option value="aula_virtual_plataforma">Aula Virtual / Plataforma</option>
          <option value="administracion_gestion">Atención Administrativa</option>
          <option value="felicitaciones_general">Felicitaciones</option>
          <option value="sugerencias_mejora">Sugerencias de Mejora</option>
          <option value="otro">Otros</option>
        </select>

        {/* Búsqueda por texto libre */}
        <form onSubmit={manejarEnvioBusqueda} style={{ display: "flex", gap: "0.4rem", flex: 1, minWidth: "200px" }}>
          <div style={{ position: "relative", width: "100%" }}>
            <input
              type="text"
              className="text-input"
              style={{ width: "100%", paddingLeft: "2.2rem" }}
              placeholder="Buscar palabras clave en opiniones..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
            <Search size={16} style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
          </div>
          <button type="submit" className="btn btn-secondary btn-sm">Buscar</button>
        </form>
      </div>

      {/* Lista de Comentarios */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "450px", overflowY: "auto", paddingRight: "0.25rem" }}>
        {comentarios.length > 0 ? (
          comentarios.map((c) => {
            const esNegativo = c.sentiment === "negativo";
            return (
              <div
                key={c.id}
                style={{
                  background: esNegativo ? "#fffdfd" : "white",
                  border: esNegativo ? "1px solid #fca5a5" : "1px solid var(--border-color)",
                  borderLeft: esNegativo ? "4px solid var(--danger)" : "1px solid var(--border-color)",
                  borderRadius: "8px",
                  padding: "0.9rem 1.1rem",
                  boxShadow: "var(--shadow-sm)",
                  transition: "transform 0.1s ease",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.4rem", flexWrap: "wrap", gap: "0.4rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    {obtenerBadgeSentimiento(c.sentiment)}
                    <span className="badge badge-topic">{c.topic_label}</span>
                  </div>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 500 }}>
                    {c.course_name}
                  </span>
                </div>
                <p style={{ fontSize: "0.9rem", color: esNegativo ? "#7f1d1d" : "var(--text-main)", fontStyle: "italic", lineHeight: 1.5 }}>
                  "{c.text}"
                </p>
              </div>
            );
          })
        ) : (
          <div style={{ textAlign: "center", padding: "2.5rem 1rem", color: "var(--text-muted)", fontSize: "0.9rem" }}>
            <AlertCircle size={28} style={{ margin: "0 auto 0.5rem auto", opacity: 0.5 }} />
            <p>No se encontraron comentarios que coincidan con los filtros seleccionados.</p>
          </div>
        )}
      </div>
    </div>
  );
}
