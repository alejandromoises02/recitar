import { Platform, ScrollView, Text, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fluid } from "../../../design/fluid";
import { spacing, typography } from "../../../design/tokens";
import { homeLayout } from "../application/home-layout";
import { BrandLogo } from "./BrandLogo";
import { HomeSection } from "./HomeSection";
import { PHONE_WIDTH } from "./HomeScreen.constants";
import { headlineSizing, styles } from "./HomeScreen.styles";
import { homeStrings } from "./strings";

export function HomeScreen() {
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const layout = homeLayout(width);
  const gutter = width < PHONE_WIDTH ? spacing.md : spacing.xl;
  // iOS insets the content under the status bar by itself; Android draws edge to edge.
  const paddingTop = Platform.OS === "android" ? insets.top + spacing.md : spacing.md;

  return (
    <ScrollView
      style={styles.screen}
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={[styles.content, { paddingHorizontal: gutter, paddingTop }]}
    >
      <BrandLogo size={fluid(typography.logo.size, width)} />
      <Text accessibilityRole="header" style={[styles.headline, headlineSizing(fluid(typography.display.size, width))]}>
        {homeStrings.headlineLead}
        <Text style={styles.city}>{homeStrings.headlineCity}</Text>
      </Text>

      {layout.kind === "stacked" ? (
        layout.order.map((section) => <HomeSection key={section} section={section} />)
      ) : (
        <>
          <View style={styles.hero}>
            <View style={{ flex: layout.leftShare }}>
              <HomeSection section={layout.left} />
            </View>
            <View style={{ flex: 1 - layout.leftShare }}>
              <HomeSection section={layout.right} />
            </View>
          </View>
          {layout.below.map((section) => (
            <HomeSection key={section} section={section} />
          ))}
        </>
      )}
    </ScrollView>
  );
}
