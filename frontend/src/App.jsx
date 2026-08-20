import React, { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import BarraNavegacion from "./components/BarraNavegacion";
import ModalCarga from "./components/ModalCarga";
import ModalGestionDatos from "./components/ModalGestionDatos";
import BarraFiltros from "./components/BarraFiltros";
import TarjetasKpi from "./components/TarjetasKpi";
import GraficosPreguntas from "./components/GraficosPreguntas";
import PanelIa from "./components/PanelIa";
import ExploradorComentarios from "./components/ExploradorComentarios";
import TablaCursos from "./components/TablaCursos";
import GraficoTendencias from "./components/GraficoTendencias";
import {
  fetchCourses,
  fetchKpis,
  fetchQuestions,
  fetchCoursesComparison,
  fetchTrends,
  fetchAiInsights,
} from "./servicios/api";

export default function App() {
  const [cursos, setCursos] = useState([]);
  const [cursoSeleccionado, setCursoSeleccionado] = useState(null);
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [modalCargaAbierto, setModalCargaAbierto] = useState(false);
  const [modalGestionAbierto, setModalGestionAbierto] = useState(false);
  const [cargando, setCargando] = useState(true);

  const [kpis, setKpis] = useState(null);
  const [datosPreguntas, setDatosPreguntas] = useState([]);
  const [comparacionCursos, setComparacionCursos] = useState([]);
  const [tendencias, setTendencias] = useState([]);
  const [datosIa, setDatosIa] = useState(null);

  const filtrosActuales = {
    course_id: cursoSeleccionado,
    start_date: fechaInicio || undefined,
    end_date: fechaFin || undefined,
  };

  const cargarCursos = async () => {
    try {
      const data = await fetchCourses();
      setCursos(data || []);
    } catch (err) {
      console.error("Error al cargar cursos:", err);
    }
  };

  const cargarTablero = async () => {
    setCargando(true);

    try {
      const [resKpis, resPreguntas, resComp, resTendencias, resIa] = await Promise.all([
        fetchKpis(filtrosActuales),
        fetchQuestions(filtrosActuales),
        fetchCoursesComparison(filtrosActuales),
        fetchTrends(filtrosActuales),
        fetchAiInsights(filtrosActuales),
      ]);

      setKpis(resKpis);
      setDatosPreguntas(resPreguntas || []);
      setComparacionCursos(resComp || []);
      setTendencias(resTendencias || []);
      setDatosIa(resIa);
    } catch (err) {
      console.error("Error al cargar datos del tablero:", err);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarCursos();
  }, []);

  useEffect(() => {
    cargarTablero();
  }, [cursoSeleccionado, fechaInicio, fechaFin]);

  const limpiarFiltros = () => {
    setCursoSeleccionado(null);
    setFechaInicio("");
    setFechaFin("");
  };

  const alActualizarDatos = () => {
    cargarCursos();
    cargarTablero();
  };

  return (
    <div className="app-container">
      <BarraNavegacion
        alAbrirCarga={() => setModalCargaAbierto(true)}
        alAbrirGestion={() => setModalGestionAbierto(true)}
        alActualizar={cargarTablero}
        cargando={cargando}
        filtros={filtrosActuales}
      />

      <main className="main-content">
        <BarraFiltros
          cursos={cursos}
          cursoSeleccionado={cursoSeleccionado}
          alSeleccionarCurso={setCursoSeleccionado}
          fechaInicio={fechaInicio}
          setFechaInicio={setFechaInicio}
          fechaFin={fechaFin}
          setFechaFin={setFechaFin}
          alLimpiar={limpiarFiltros}
        />

        {cargando && !kpis ? (
          <div
            className="card"
            style={{
              textAlign: "center",
              padding: "4rem 2rem",
              background: "white",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "1rem",
            }}
          >
            <Loader2 size={40} className="spin" style={{ color: "var(--primary)" }} />
            <p style={{ color: "var(--text-muted)", fontSize: "1rem", fontWeight: 600 }}>
              Calculando métricas y análisis de encuestas...
            </p>
          </div>
        ) : kpis && kpis.total_surveys > 0 ? (
          <>
            {/* Tarjetas de Métricas Clave */}
            <TarjetasKpi kpis={kpis} />

            {/* Desglose de Preguntas 1 a 8 */}
            <GraficosPreguntas datosPreguntas={datosPreguntas} />

            {/* Fila: Panel de IA + Evolución Temporal */}
            <div className="grid-2">
              <PanelIa datosIa={datosIa} alRecargar={cargarTablero} />
              <GraficoTendencias tendencias={tendencias} />
            </div>

            {/* Comparativa por curso */}
            <TablaCursos comparacionCursos={comparacionCursos} />

            {/* Explorador de Comentarios de Alumnos */}
            <ExploradorComentarios cursoSeleccionado={cursoSeleccionado} />
          </>
        ) : (
          <div
            className="card"
            style={{
              textAlign: "center",
              padding: "4rem 2rem",
              background: "white",
              border: "2px dashed var(--border-color)",
            }}
          >
            <h3 style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "0.5rem" }}>
              No hay encuestas registradas todavía
            </h3>
            <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", maxWidth: "500px", margin: "0 auto 1.5rem auto" }}>
              Hacé clic en el botón a continuación para subir uno o múltiples archivos CSV o Excel exportados de Campus Córdoba.
            </p>
            <button className="btn btn-primary" onClick={() => setModalCargaAbierto(true)}>
              Cargar Archivos de Encuestas
            </button>
          </div>
        )}
      </main>

      <ModalCarga
        estaAbierto={modalCargaAbierto}
        alCerrar={() => setModalCargaAbierto(false)}
        alCompletarCarga={alActualizarDatos}
      />

      <ModalGestionDatos
        estaAbierto={modalGestionAbierto}
        alCerrar={() => setModalGestionAbierto(false)}
        cursos={cursos}
        alActualizarDatos={alActualizarDatos}
      />
    </div>
  );
}
