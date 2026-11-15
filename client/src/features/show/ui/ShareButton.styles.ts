import { StyleSheet } from "react-native";
import { colors, fontFamily, radius, spacing, touchTarget } from "../../../design/tokens";

export const styles = StyleSheet.create({
  wrap: { alignItems: "flex-end" },
  button: {
    width: touchTarget,
    height: touchTarget,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
  },
  pressed: { backgroundColor: colors.line },
  // Floats under the button, so it never adds height to the title row.
  copied: { position: "absolute", top: touchTarget + spacing.hair, right: 0, width: 120, textAlign: "right", fontFamily: fontFamily.body, fontSize: 11, color: colors.textMuted },
  hidden: { opacity: 0 },
});
