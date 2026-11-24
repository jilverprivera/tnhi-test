# Entregables del caso (PDF en español)

| PDF | Contenido |
|---|---|
| [`2-documento-de-arquitectura.pdf`](2-documento-de-arquitectura.pdf) | 3 páginas con diagrama: componentes y flujo, dónde interviene la IA y dónde no, cómo se sabe que acierta, costos, tiempo ahorrado, deuda técnica y qué cambia si TAC solo autoriza su suite (Microsoft 365 / Google Workspace). |
| [`3-como-trabaje-con-la-ia.pdf`](3-como-trabaje-con-la-ia.pdf) | Archivos de instrucciones, prompts del sistema de la solución y bitácora. Los anexos se toman del repositorio al generar el PDF. |
| [`4-evaluacion.pdf`](4-evaluacion.pdf) | Método, resultados por campo y por documento (8/8 y 17/17), escenario sin OCR, errores encontrados y qué se hizo con ellos. |
| [`5-nota-para-martha.pdf`](5-nota-para-martha.pdf) | Una página, sin jerga: cómo se usa y qué tiene que revisar ella. |
| [`6-guia-de-entrevista.pdf`](6-guia-de-entrevista.pdf) | **Uso interno del candidato.** Mensaje en 30 segundos, guion por fases con tiempos y frases clave, plan B si falla la demo, 42 preguntas de reclutador con respuesta (10 marcadas como probables), números de memoria, errores a evitar y preguntas para ellos. |

Las fuentes editables están en `fuentes/` (HTML + `estilos.css`). Para regenerar los PDF, desde la raíz del repositorio y con `web/node_modules` instalado:

```bash
node entregables/generar-pdfs.mjs
```

La evaluación del entregable 4 se reproduce con:

```bash
cd api && uv run python -m app.evaluate --data-dir /tmp/docket-eval --json /tmp/docket-eval.json
```

La documentación técnica completa (por feature, en español e inglés) está en `docs/`.
