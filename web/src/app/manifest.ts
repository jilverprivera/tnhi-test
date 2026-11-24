import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Docket · Radicación TAC",
    short_name: "Docket",
    description: "Radicación asistida de correspondencia para Terminales Andinas de Carga.",
    lang: "es-CO",
    start_url: "/inbox",
    scope: "/",
    display: "standalone",
    orientation: "any",
    background_color: "#fff9f3",
    theme_color: "#0f6b63",
    categories: ["business", "productivity"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Bandeja", url: "/inbox" },
      { name: "Vencimientos", url: "/deadlines" },
    ],
  };
}
