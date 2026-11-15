import { Text, View } from "react-native";
import { Pulse } from "../../home/ui/skeleton/Pulse";
import { styles } from "./ShowSkeleton.styles";

/** While the show loads: blocks shaped like the poster, the name and the date tiles. */
export function ShowSkeleton({ label, oneColumn }: { label: string; oneColumn: boolean }) {
  return (
    <View style={[styles.layout, oneColumn && styles.oneColumn]} aria-busy>
      <Text style={styles.hidden}>{label}</Text>
      <Pulse style={[styles.block, styles.poster, oneColumn && styles.posterOneColumn]} />
      <View style={styles.info}>
        <Pulse style={[styles.block, styles.name]} />
        <Pulse style={[styles.block, styles.meta]} />
        <Pulse style={[styles.block, styles.tiles]} />
      </View>
    </View>
  );
}
