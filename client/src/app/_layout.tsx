import { QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { useState } from "react";
import { useRefetchOnAppFocus } from "@/api/app-focus";
import { createQueryClient } from "@/api/query-client";

export default function RootLayout() {
  const [queryClient] = useState(createQueryClient);
  useRefetchOnAppFocus();
  return (
    <QueryClientProvider client={queryClient}>
      <Stack />
    </QueryClientProvider>
  );
}
