import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import sitemap from "@astrojs/sitemap";

const normalizeBasePath = (value) => {
  if (!value || value === "/") {
    return "/";
  }

  const withLeadingSlash = value.startsWith("/") ? value : `/${value}`;
  return withLeadingSlash.endsWith("/") ? withLeadingSlash.slice(0, -1) : withLeadingSlash;
};

const siteUrl = process.env.PUBLIC_SITE_URL || "https://raff-dev.github.io";
const basePath = normalizeBasePath(process.env.PUBLIC_BASE_PATH || "/goose");

export default defineConfig({
  output: "static",
  site: siteUrl,
  base: basePath,
  integrations: [tailwind(), sitemap()],
});
