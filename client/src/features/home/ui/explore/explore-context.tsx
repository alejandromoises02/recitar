import type { ReactNode } from "react";
import { createContext, useContext } from "react";
import type { Explore } from "./use-explore";

const ExploreContext = createContext<Explore | null>(null);

/** Shares one explore state between the filter panel (list header) and the listing rows. */
export function ExploreProvider({ value, children }: { value: Explore; children: ReactNode }) {
  return <ExploreContext.Provider value={value}>{children}</ExploreContext.Provider>;
}

export function useExploreContext(): Explore {
  const explore = useContext(ExploreContext);
  if (!explore) throw new Error("useExploreContext needs an ExploreProvider");
  return explore;
}
