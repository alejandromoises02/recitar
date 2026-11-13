import { StyleSheet, Text, View } from "react-native";
import { brandShadow, colors, fontFamily } from "../../../design/tokens";

type Props = { size: number };

/** "recitAR" in the logo face with its stepped filete shadow: red, an ink gap, then blue, each a
 * copy of the word offset down and right (DESIGN.md). Only the top copy is read by screen readers. */
export function BrandLogo({ size }: Props) {
  const text = { fontFamily: fontFamily.logo, fontSize: size, lineHeight: size * 1.15 };
  const layers = [...brandShadow].reverse(); // farthest first, so nearer layers paint over it
  return (
    <View accessibilityRole="header" accessibilityLabel="recitAR">
      {layers.map(({ offset, color }) => (
        <Text
          key={offset}
          aria-hidden
          importantForAccessibility="no-hide-descendants"
          style={[text, styles.layer, { color, transform: [{ translateX: offset * size }, { translateY: offset * size }] }]}
        >
          recitAR
        </Text>
      ))}
      <Text aria-hidden style={[text, { color: colors.accent }]}>
        recitAR
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  layer: { position: "absolute", left: 0, top: 0 },
});
