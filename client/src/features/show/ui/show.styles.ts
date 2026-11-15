import type { TextStyle } from "react-native";
import { colors, typography } from "../../../design/tokens";

/** A section title on the show page ("Fechas", "Más en <venue>"). */
export const sectionTitle: TextStyle = { fontFamily: typography.headline.fontFamily, fontSize: 18, color: colors.text };
