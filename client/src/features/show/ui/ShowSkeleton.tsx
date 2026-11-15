import { Text, View } from "react-native";
import { styles } from "./ShowSkeleton.styles";

/** While the show loads: blocks shaped like the poster, the name and the date tiles. */
export function ShowSkeleton({ label, oneColumn }: { label: string; oneColumn: boolean }) {
  return (
    <View style={[styles.layout, oneColumn && styles.oneColumn]} aria-busy>
      <Text style={styles.hidden}>{label}</Text>
      <View style={[styles.block, styles.poster, oneColumn && styles.posterOneColumn]} />
      <View style={styles.info}>
        <View style={[styles.block, styles.name]} />
        <View style={[styles.block, styles.meta]} />
        <View style={[styles.block, styles.tiles]} />
      </View>
    </View>
  );
}
