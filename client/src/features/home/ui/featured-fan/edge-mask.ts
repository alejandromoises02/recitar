import type { ViewStyle } from "react-native";

/** Native has no CSS mask: the fan simply clips at its box (on phones, the screen edge). */
export const edgeMask: ViewStyle | undefined = undefined;
