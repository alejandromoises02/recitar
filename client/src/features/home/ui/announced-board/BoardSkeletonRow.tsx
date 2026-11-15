import { Pulse } from "../skeleton/Pulse";
import type { BoardGeometry } from "./board.constants";
import { ROW_HEIGHT_EM } from "./board.constants";
import { styles } from "./BoardRow.styles";
import { Flap } from "./Flap";

export function BoardSkeletonRow({ geometry }: { geometry: BoardGeometry }) {
  const minHeight = geometry.flapSize * ROW_HEIGHT_EM;
  return (
    <Pulse style={styles.row}>
      <Flap style={{ width: geometry.dateWidth, minHeight }} />
      <Flap style={[styles.nameFlap, { minHeight }]} />
    </Pulse>
  );
}
