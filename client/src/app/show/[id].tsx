import { useLocalSearchParams } from "expo-router";
import { ShowScreen } from "@/features/show/ui/ShowScreen";

export default function ShowRoute() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <ShowScreen id={id} />;
}
