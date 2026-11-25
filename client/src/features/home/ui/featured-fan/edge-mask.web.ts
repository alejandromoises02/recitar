import type { ViewStyle } from "react-native";
import { EDGE_FADE_SHARE } from "./featured.constants";

const fade = `linear-gradient(90deg, transparent, #000 ${EDGE_FADE_SHARE}, #000 calc(100% - ${EDGE_FADE_SHARE}), transparent)`;

/**
 * The sleeves fade out at the fan's sides through a mask, so whatever lies behind (the page tint)
 * shows through instead of a band of flat background colour. react-native-web passes maskImage on and adds the -webkit- prefix.
 */
export const edgeMask = { maskImage: fade } as ViewStyle;
