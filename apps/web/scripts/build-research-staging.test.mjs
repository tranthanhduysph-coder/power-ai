import test from "node:test";
import assert from "node:assert/strict";
import { stagingApiUrl } from "./build-research-staging.mjs";

test("staging browser build targets only the separate staging API", () => {
  assert.equal(stagingApiUrl("https://power-research-staging-api.onrender.com"),
    "https://power-research-staging-api.onrender.com/api/v1");
  assert.equal(stagingApiUrl("https://power-research-staging-api-ab12.onrender.com/"),
    "https://power-research-staging-api-ab12.onrender.com/api/v1");
  for (const value of ["https://power-ai-nl09.onrender.com", "http://power-research-staging-api.onrender.com",
    "https://power-research-staging-api.onrender.com/path", "https://example.invalid",
    "https://secret@power-research-staging-api.onrender.com", "https://power-research-staging-api.onrender.com?q=1"]) {
    assert.throws(() => stagingApiUrl(value));
  }
});
