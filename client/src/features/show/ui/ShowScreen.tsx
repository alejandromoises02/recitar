import { router } from "expo-router";
import Head from "expo-router/head";
import { useState } from "react";
import { ScrollView, View, useWindowDimensions } from "react-native";
import { spacing } from "../../../design/tokens";
import { configuredApiBase } from "../../events/infrastructure/events-api";
import { useShow } from "../../events/infrastructure/events-queries";
import { ONE_COLUMN_WIDTH } from "./show.constants";
import { ShowHeader } from "./ShowHeader";
import { ShowMessage } from "./ShowMessage";
import { ShowPage } from "./ShowPage";
import { styles } from "./ShowScreen.styles";
import { ShowSkeleton } from "./ShowSkeleton";
import { useShowStrings } from "./strings";

/** /show/<id>: the page once loaded, else its skeleton, the load error or the unknown-show message. */
export function ShowScreen({ id }: { id: string }) {
  const strings = useShowStrings();
  const [apiBase] = useState(configuredApiBase);
  const { width } = useWindowDimensions();
  const query = useShow(id);
  if (query.data) return <ShowPage show={query.data} apiBase={apiBase} />;

  const oneColumn = width <= ONE_COLUMN_WIDTH;
  return (
    <View style={styles.screen}>
      <Head>
        <title>{query.isPending ? "recitAR" : `${query.isError ? strings.loadFailed : strings.notFoundTitle} · recitAR`}</title>
      </Head>
      <ScrollView contentContainerStyle={[styles.content, { paddingHorizontal: width < 600 ? spacing.md : spacing.xl }]}>
        <ShowHeader compact={oneColumn} />
        <View role="main">
          {query.isPending ? (
            <ShowSkeleton label={strings.loading} oneColumn={oneColumn} />
          ) : query.isError ? (
            <ShowMessage title={strings.loadFailed} action={strings.retry} onAction={() => query.refetch()} alert />
          ) : (
            <ShowMessage title={strings.notFoundTitle} body={strings.notFoundBody} action={strings.goToListing} onAction={() => router.replace("/")} />
          )}
        </View>
      </ScrollView>
    </View>
  );
}
