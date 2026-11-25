import { useState } from "react";
import { Platform, Pressable, Share, Text, View } from "react-native";
import { ShareIcon } from "./ShareIcon";
import { styles } from "./ShareButton.styles";
import { useShowStrings } from "./strings";
import { useShareImage } from "./use-share-image";

type Props = { title: string; message: string; url: string; imageUrl?: string | null; onShare?: () => void };

/**
 * The native share sheet on phones; on web the browser's share, with the show's image when the
 * browser can share files, else the message and link copied to the clipboard.
 */
export function ShareButton({ title, message, url, imageUrl, onShare }: Props) {
  const strings = useShowStrings();
  const [copied, setCopied] = useState(false);
  const image = useShareImage(imageUrl);
  const withLink = `${message} ${url}`;
  const share = async () => {
    onShare?.();
    if (Platform.OS !== "web") {
      await Share.share({ title, message: withLink, url });
      return;
    }
    if (typeof navigator.share === "function") {
      // With a file, some apps drop the url field, so the link travels inside the text.
      const data = image ? { title, text: withLink, files: [image] } : { title, text: message, url };
      await navigator.share(data).catch(() => undefined);
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
