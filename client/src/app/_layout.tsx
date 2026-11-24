import { QueryClientProvider } from "@tanstack/react-query";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import { StatusBar } from "expo-status-bar";
import { useEffect, useState } from "react";
import { Platform } from "react-native";
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

  // A font that fails falls back to the system one. The web build's pre-rendered HTML already declares
  // every font (@font-face) and renders the whole page: waiting here would make the browser's first
  // render empty, unlike that HTML, and React would throw the page away and paint it again.
  const ready = Platform.OS === "web" || fontsLoaded || fontError !== null;
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
