import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Campus Connect (placeholder name — see R&D doc Section 29)",
    short_name: "CampusConnect",
    description:
      "Small, real-world actions toward student connection — not another mood tracker.",
    start_url: "/",
    display: "standalone",
    background_color: "#faf8f5",
    theme_color: "#3f6e63",
    orientation: "portrait-primary",
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
