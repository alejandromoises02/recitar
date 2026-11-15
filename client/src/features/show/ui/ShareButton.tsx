import { useState } from "react";
import { Platform, Pressable, Share, Text, View } from "react-native";
import { ShareIcon } from "./ShareIcon";
import { styles } from "./ShareButton.styles";
import { useShowStrings } from "./strings";

type Props = { title: string; url: string };

/** The native share sheet on phones; on web the browser's share, else the link copied to the clipboard. */
export function ShareButton({ title, url }: Props) {
  const strings = useShowStrings();
  const [copied, setCopied] = useState(false);
  const share = async () => {
    if (Platform.OS !== "web") {
      await Share.share({ title, message: `${title} ${url}`, url });
      return;
    }
    if (typeof navigator.share === "function") {
      await navigator.share({ title, url }).catch(() => undefined);
      return;
    }
    await navigator.clipboard?.writeText(url);
    setCopied(true);
  };
  return (
    <View style={styles.wrap}>
      <Pressable accessibilityRole="button" accessibilityLabel={strings.share} onPress={share} style={({ pressed }) => [styles.button, pressed && styles.pressed]}>
        <ShareIcon />
      </Pressable>
      <Text style={[styles.copied, !copied && styles.hidden]} aria-live="polite">
        {copied ? strings.linkCopied : ""}
      </Text>
    </View>
  );
}
