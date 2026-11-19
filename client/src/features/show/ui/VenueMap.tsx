import * as Linking from "expo-linking";
import { View } from "react-native";
import { WebView } from "react-native-webview";
import { mapEmbedPage } from "../application/show-page";
import { EMBED_PREFIXES } from "./VenueMap.constants";
import { styles } from "./VenueMap.styles";

type Props = { url: string; label: string };

const staysInMap = (url: string) => EMBED_PREFIXES.some((prefix) => url.startsWith(prefix));

/** The venue on Google's embedded map, inside a page of its own (Google serves the embed only in an iframe).
 * Its links ("open in Maps", directions) open the maps app or the browser. */
export function VenueMap({ url, label }: Props) {
  return (
    <View style={styles.frame} accessibilityLabel={label}>
      <WebView
        source={{ html: mapEmbedPage(url) }}
        style={styles.map}
        originWhitelist={["*"]}
        setSupportMultipleWindows
        onOpenWindow={(event) => void Linking.openURL(event.nativeEvent.targetUrl)}
        onShouldStartLoadWithRequest={(request) => {
          if (!request.isTopFrame || staysInMap(request.url)) return true;
          void Linking.openURL(request.url);
          return false;
        }}
      />
    </View>
  );
}
