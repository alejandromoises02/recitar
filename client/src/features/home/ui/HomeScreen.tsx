import { Platform, ScrollView, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fluid } from "../../../design/fluid";
import { colors, fontFamily, spacing, typography } from "../../../design/tokens";
import type { HomeSection } from "../application/home-layout";
import { homeLayout } from "../application/home-layout";
import { BrandLogo } from "./BrandLogo";
import { NextUpStrip } from "./NextUpStrip";
import { SectionSlot } from "./SectionSlot";
import { homeStrings } from "./strings";

/** Rough heights the real sections will take, so the frame already reads like the mock. */
const SLOT_HEIGHT: Record<HomeSection, number> = { featured: 420, justAnnounced: 360, next: 200, explore: 480 };

/** The built sections; the others are still placeholders (cli02 T3-T6). */
function Section({ section }: { section: HomeSection }) {
  if (section === "next") return <NextUpStrip />;
  return <SectionSlot section={section} minHeight={SLOT_HEIGHT[section]} />;
}

export function HomeScreen() {
  const { width } = useWindowDimensions();
  const insets = useSafeAreaInsets();
  const layout = homeLayout(width);
  const gutter = width < 600 ? spacing.md : spacing.xl;
  const headlineSize = fluid(typography.display.size, width);

  return (
    <ScrollView
      style={styles.screen}
      // iOS insets the content under the status bar by itself; Android draws edge to edge.
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={[
        styles.content,
        { paddingHorizontal: gutter, paddingTop: Platform.OS === "android" ? insets.top + spacing.md : spacing.md },
      ]}
    >
      <BrandLogo size={fluid(typography.logo.size, width)} />
      <Text
        accessibilityRole="header"
        style={[
          styles.headline,
          {
            fontSize: headlineSize,
            lineHeight: headlineSize * 1.05,
            letterSpacing: typography.display.letterSpacing * headlineSize,
          },
        ]}
      >
        {homeStrings.headlineLead}
        <Text style={styles.city}>{homeStrings.headlineCity}</Text>
      </Text>

      {layout.kind === "stacked" ? (
        layout.order.map((section) => <Section key={section} section={section} />)
      ) : (
        <>
          <View style={styles.hero}>
            <View style={{ flex: layout.leftShare }}>
              <SectionSlot section={layout.left} minHeight={SLOT_HEIGHT[layout.right]} />
            </View>
            <View style={{ flex: 1 - layout.leftShare }}>
              <SectionSlot section={layout.right} minHeight={SLOT_HEIGHT[layout.right]} />
            </View>
          </View>
          {layout.below.map((section) => (
            <Section key={section} section={section} />
          ))}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { gap: spacing.lg, paddingBottom: spacing.xxxl },
  headline: { fontFamily: typography.display.fontFamily, color: colors.text, maxWidth: 900 },
  city: { fontFamily: fontFamily.logo, color: colors.accent },
  hero: { flexDirection: "row", gap: spacing.xl, alignItems: "stretch" },
});
