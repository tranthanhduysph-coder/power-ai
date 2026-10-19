import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

export function stagingApiUrl(rawOrigin) {
  const origin = new URL(rawOrigin);
  if (origin.protocol !== "https:" || origin.username || origin.password ||
    origin.port || origin.pathname !== "/" || origin.search || origin.hash ||
    !/^power-research-staging-api(?:-[a-z0-9]+)?\.onrender\.com$/.test(origin.hostname)) {
    throw new Error("Refusing to build research staging against a non-staging API");
  }
  return `${origin.origin}/api/v1`;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const apiUrl = stagingApiUrl(process.env.RESEARCH_STAGING_API_ORIGIN || "");
  const result = spawnSync("npm", ["run", "build"], {
    stdio: "inherit",
    env: { ...process.env, NEXT_PUBLIC_API_URL: apiUrl },
  });
  if (result.error) throw result.error;
  process.exit(result.status ?? 1);
}
