import { focusManager } from "@tanstack/react-query";
import { useEffect } from "react";
import { AppState, type AppStateStatus, Platform } from "react-native";

/**
 * Lets queries refresh when the app comes back to the foreground, as they do on web when the tab
 * regains focus. From the TanStack Query React Native guide.
 */
export function useRefetchOnAppFocus(): void {
  useEffect(() => {
    if (Platform.OS === "web") return; // the browser's focus events already do this
    const onChange = (status: AppStateStatus) => focusManager.setFocused(status === "active");
    const subscription = AppState.addEventListener("change", onChange);
    return () => subscription.remove();
  }, []);
}
