import { AlfaSlabOne_400Regular } from "@expo-google-fonts/alfa-slab-one";
import { BarlowCondensed_700Bold } from "@expo-google-fonts/barlow-condensed";
import { Onest_400Regular, Onest_600SemiBold } from "@expo-google-fonts/onest";
import { Unbounded_500Medium, Unbounded_600SemiBold } from "@expo-google-fonts/unbounded";
import type { FontName } from "./tokens";

/**
 * Every family in tokens.fontFamily, loaded at start-up with useFonts (see app/_layout.tsx). Loaded
 * at runtime rather than embedded with the expo-font config plugin because the app is tried in
 * Expo Go, which cannot embed fonts; switch to the plugin when the app gets its own build.
 * `satisfies` makes a family missing here a type error.
 */
export const fontAssets = {
  AlfaSlabOne_400Regular,
  Unbounded_500Medium,
  Unbounded_600SemiBold,
  Onest_400Regular,
  Onest_600SemiBold,
  BarlowCondensed_700Bold,
} satisfies Record<FontName, number>;
