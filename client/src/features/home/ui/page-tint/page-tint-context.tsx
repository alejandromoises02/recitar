import type { ReactNode } from "react";
import { createContext, useContext, useState } from "react";

const SetTintContext = createContext<(uri: string | null) => void>(() => {});
const TintContext = createContext<string | null>(null);

/**
 * The featured fan reports the centre show's image and the page tint draws it. The setter and the
 * value live in separate contexts so the fan, which only sets, does not re-render on each change.
 */
export function PageTintProvider({ children }: { children: ReactNode }) {
  const [uri, setUri] = useState<string | null>(null);
  return (
    <SetTintContext.Provider value={setUri}>
      <TintContext.Provider value={uri}>{children}</TintContext.Provider>
    </SetTintContext.Provider>
  );
}

export const useSetPageTint = () => useContext(SetTintContext);
export const usePageTint = () => useContext(TintContext);
