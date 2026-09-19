import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Coo_Do",
    short_name: "Coo_Do",
    description:
      "Small, real-world actions toward connection and wellbeing.",
    start_url: "/",
    display: "standalone",
    background_color: "#faf9ff",
    theme_color: "#6841d8",
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
      {
        src: "/icons/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
