import { useEffect, useState } from "react";
import { AppState } from "react-native";

/**
 * Whether the app is in the foreground. iOS keeps a WebView's audio playing after the app goes to the
 * background, so the app's Spotify players are removed meanwhile (the web keeps playing across tabs).
 */
export function useAppActive(): boolean {
  const [active, setActive] = useState(AppState.currentState === "active");
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (state) => setActive(state === "active"));
    return () => subscription.remove();
  }, []);
  return active;
}
