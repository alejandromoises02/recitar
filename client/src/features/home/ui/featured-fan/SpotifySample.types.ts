import type { Ref } from "react";

/** What the record (the play button) asks of the sample player. */
export type SampleHandle = { toggle: () => void };

export type SampleProps = {
  artistId: string;
  label: string;
  /** Called on every playback change: true while it plays. */
  onPlaying: (playing: boolean) => void;
  ref?: Ref<SampleHandle>;
};
