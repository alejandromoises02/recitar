import { Pressable, Text, View } from "react-native";
import { heading } from "../../home/ui/a11y";
import { styles } from "./ShowMessage.styles";

type Props = { title: string; body?: string; action: string; onAction: () => void; alert?: boolean };

/** A page-sized message with one action: the load error (retry) and the unknown show (back to the listing). */
export function ShowMessage({ title, body, action, onAction, alert = false }: Props) {
  return (
    <View style={styles.box}>
      <Text style={styles.title} {...heading(1)}>
        {title}
      </Text>
      {body ? (
        <Text style={styles.body} role={alert ? "alert" : undefined}>
          {body}
        </Text>
      ) : null}
      <Pressable accessibilityRole="button" onPress={onAction} style={({ pressed }) => [styles.button, pressed && styles.pressed]}>
        <Text style={styles.buttonText}>{action}</Text>
      </Pressable>
    </View>
  );
}
