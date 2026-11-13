/** Home UI copy. The English table comes with cli02 T7. */
export const homeStrings = {
  headlineLead: "Lo nuevo en la cartelera de ",
  headlineCity: "Buenos Aires",
  sections: {
    featured: "Destacados",
    justAnnounced: "Recién anunciados",
    next: "Próximos",
    explore: "Toda la cartelera",
  },
  loading: "Cargando…",
  loadFailed: "No pudimos cargar esta sección.",
  retry: "Reintentar",
  scrollBack: "Ver anteriores",
  scrollMore: "Ver más próximos",
  shows: (count: number, more: boolean) => `${count}${more ? "+" : ""} ${count === 1 ? "show" : "shows"}`,
  featured: {
    carousel: "Carrusel de destacados",
    tag: { picked: "Destacado", just_announced: "Recién anunciado" },
    cta: "Ver fechas y entradas",
    ticketsAt: "Entradas en",
    trust: "recitAR no vende entradas: te lleva a la página oficial de cada show.",
    pause: "Pausar",
    play: "Reproducir",
    previous: "Show anterior",
    next: "Show siguiente",
  },
} as const;
