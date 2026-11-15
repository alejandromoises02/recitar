import { StyleSheet } from "react-native";
import { BLOCK_GAP, CARD_GAP } from "./explore.constants";

export const styles = StyleSheet.create({
  blocks: { flexDirection: "row", alignItems: "flex-start", gap: BLOCK_GAP },
  cards: { flexDirection: "row", alignItems: "stretch", gap: CARD_GAP },
});
