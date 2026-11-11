import { readFileSync } from "node:fs";
import openapiTS, { astToString, COMMENT_HEADER } from "openapi-typescript";
import { describe, expect, it } from "vitest";

const here = new URL(".", import.meta.url);

describe("schema.ts", () => {
  it("is what openapi.json generates (run `npm run gen:api` after updating openapi.json)", async () => {
    const generated = COMMENT_HEADER + astToString(await openapiTS(new URL("openapi.json", here)));
    expect(readFileSync(new URL("schema.ts", here), "utf8")).toBe(generated);
  });
});
