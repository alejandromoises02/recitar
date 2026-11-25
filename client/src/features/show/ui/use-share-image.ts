import { useEffect, useState } from "react";
import { Platform } from "react-native";
import { SHARE_FILE_NAME } from "./ShareButton.constants";

/**
 * Web only: the show's image as a file the browser can share, fetched ahead of the tap. Safari only
 * shares while the tap is still fresh, so the image cannot be downloaded after it. Null when the
 * browser cannot share files, the image is not readable from this page (another site's image
 * without CORS) or anything fails: the share then goes out without it.
 */
export function useShareImage(url: string | null | undefined): File | null {
  const [loaded, setLoaded] = useState<{ url: string; file: File } | null>(null);
  useEffect(() => {
    if (Platform.OS !== "web" || !url || typeof navigator.canShare !== "function") return;
    let cancelled = false;
    fetch(url)
      .then((response) => (response.ok ? response.blob() : null))
      .then((blob) => {
        if (cancelled || !blob || !blob.type.startsWith("image/")) return;
        const extension = blob.type.split("/")[1]?.split("+")[0] ?? "jpg";
        const image = new File([blob], `${SHARE_FILE_NAME}.${extension}`, { type: blob.type });
        if (navigator.canShare({ files: [image] })) setLoaded({ url, file: image });
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [url]);
  // A file loaded for another show's image is never shared with this one.
  return loaded && loaded.url === url ? loaded.file : null;
}
