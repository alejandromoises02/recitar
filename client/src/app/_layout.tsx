import { QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { StatusBar } from "expo-status-bar";
import { useEffect, useState } from "react";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { useRefetchOnAppFocus } from "@/api/app-focus";
import { createQueryClient } from "@/api/query-client";
import { tracker } from "@/features/analytics/tracker";
import { fontAssets } from "@/design/fonts";
import { colors } from "@/design/tokens";
import { LangProvider } from "@/i18n/lang-context";

// Keep the splash screen up until the fonts are ready, so no screen flashes in the system font.
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [queryClient] = useState(createQueryClient);
  const [fontsLoaded, fontError] = useFonts(fontAssets);
  useRefetchOnAppFocus();
  useEffect(() => tracker().visitStarted(), []);

  const ready = fontsLoaded || fontError !== null; // a font that fails falls back to the system one
  useEffect(() => {
    if (ready) SplashScreen.hideAsync();
  }, [ready]);

  if (!ready) return null;
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <LangProvider>
          <StatusBar style="light" />
          <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.background } }} />
        </LangProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
