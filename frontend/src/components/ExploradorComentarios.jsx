import React, { useState, useEffect } from "react";
import { MessageSquare, Search } from "lucide-react";
import { fetchComments } from "../servicios/api";

export default function ExploradorComentarios({ cursoSeleccionado }) {
  const [comentarios, setComentarios] = useState([]);
  const [total, setTotal] = useState(0);
  const [tema, setTema] = useState("todos");
  const [sentimiento, setSentimiento] = useState("todos");
  const [busqueda, setBusqueda] = useState("");

  const cargarComentarios = async () => {
    try {
      const data = await fetchComments({
        course_id: cursoSeleccionado,
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
  }, [cursoSeleccionado, tema, sentimiento]);

  const manejarEnvioBusqueda = (e) => {
    e.preventDefault();
    cargarComentarios();
  };

  const obtenerBadgeSentimiento = (sent) => {
    if (sent === "positivo") return <span className="badge badge-success">Positivo</span>;
    if (sent === "negativo") return <span className="badge badge-danger">Negativo</span>;
    return <span className="badge badge-neutral">Neutro</span>;
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <MessageSquare size={20} style={{ color: "var(--primary)" }} />
            <span>Muro de Comentarios y Sugerencias Abiertas ({total})</span>
          </h3>
          <p className="card-subtitle">
            Texto literal de la Pregunta 9 clasificado automáticamente por el motor de IA
          </p>
        </div>
      </div>

      {/* Filtros de Comentarios */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1.25rem", background: "var(--bg-main)", padding: "0.75rem", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
        <form onSubmit={manejarEnvioBusqueda} style={{ display: "flex", gap: "0.5rem", flex: 1, minWidth: "220px" }}>
          <div style={{ position: "relative", width: "100%" }}>
            <input
              type="text"
              className="text-input"
              style={{ width: "100%", paddingLeft: "2.2rem" }}
              placeholder="Buscar en comentarios..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
            <Search size={16} style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
          </div>
          <button type="submit" className="btn btn-secondary btn-sm">Buscar</button>
        </form>

        <select className="select-input" style={{ minWidth: "160px" }} value={sentimiento} onChange={(e) => setSentimiento(e.target.value)}>
          <option value="todos">Todos los sentimientos</option>
          <option value="positivo">Positivos</option>
          <option value="neutro">Neutros</option>
          <option value="negativo">Negativos</option>
        </select>

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
      </div>

      {/* Lista de Comentarios */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "420px", overflowY: "auto", paddingRight: "0.25rem" }}>
        {comentarios.length > 0 ? (
          comentarios.map((c) => (
            <div
              key={c.id}
              style={{
                background: "white",
                border: "1px solid var(--border-color)",
                borderRadius: "8px",
                padding: "0.9rem 1.1rem",
                boxShadow: "var(--shadow-sm)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.4rem", flexWrap: "wrap", gap: "0.4rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  {obtenerBadgeSentimiento(c.sentiment)}
                  <span className="badge badge-topic">{c.topic_label}</span>
                </div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {c.course_name}
                </span>
              </div>
              <p style={{ fontSize: "0.9rem", color: "var(--text-main)", fontStyle: "italic", lineHeight: 1.5 }}>
                "{c.text}"
              </p>
            </div>
          ))
        ) : (
          <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)", fontSize: "0.9rem" }}>
            No se encontraron comentarios que coincidan con los filtros seleccionados.
          </div>
        )}
      </div>
    </div>
  );
}
