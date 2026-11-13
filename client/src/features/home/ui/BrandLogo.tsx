import { Text, View } from "react-native";
import { brandShadow } from "../../../design/tokens";
import { BRAND_NAME } from "./BrandLogo.constants";
import { logoText, styles } from "./BrandLogo.styles";

type Props = { size: number };

// The stepped shadow is copies of the word offset down-right, farthest painted first.
const SHADOW_LAYERS = [...brandShadow].reverse();

export function BrandLogo({ size }: Props) {
  const text = logoText(size);
  return (
    <View accessibilityRole="header" accessibilityLabel={BRAND_NAME}>
      {SHADOW_LAYERS.map(({ offset, color }) => (
        <Text
          key={offset}
          aria-hidden
          importantForAccessibility="no-hide-descendants"
          style={[text, styles.layer, { color, transform: [{ translateX: offset * size }, { translateY: offset * size }] }]}
        >
          {BRAND_NAME}
        </Text>
      ))}
      <Text aria-hidden style={[text, styles.face]}>
        {BRAND_NAME}
      </Text>
    </View>
  );
}
