import { useState } from "react";
import { Platform, Pressable, Share, Text, View } from "react-native";
import { ShareIcon } from "./ShareIcon";
import { styles } from "./ShareButton.styles";
import { useShowStrings } from "./strings";

type Props = { title: string; message: string; url: string; onShare?: () => void };

/**
 * The native share sheet on phones; on web the browser's share, else the message and link copied to
 * the clipboard. Text only: WhatsApp drops the text and link of a share that carries a file.
 */
export function ShareButton({ title, message, url, onShare }: Props) {
  const strings = useShowStrings();
  const [copied, setCopied] = useState(false);
  const withLink = `${message} ${url}`;
  const share = async () => {
    onShare?.();
    if (Platform.OS !== "web") {
      await Share.share({ title, message: withLink, url });
      return;
    }
    if (typeof navigator.share === "function") {
      await navigator.share({ title, text: message, url }).catch(() => undefined);
      return;
    }
    await navigator.clipboard?.writeText(withLink);
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
