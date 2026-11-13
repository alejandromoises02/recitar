/** Home copy, Spanish (voseo). One place, so the English option (cli02 T7) is a second table. */
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
  shows: (count: number, more: boolean) => `${count}${more ? "+" : ""} ${count === 1 ? "show" : "shows"}`,
  featuredKind: { picked: "elegidos a mano", just_announced: "recién anunciados con imagen" },
} as const;
