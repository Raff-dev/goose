const normalizeBasePath = (value: string | undefined) => {
  if (!value || value === "/") {
    return "";
  }

  const withLeadingSlash = value.startsWith("/") ? value : `/${value}`;
  return withLeadingSlash.endsWith("/") ? withLeadingSlash.slice(0, -1) : withLeadingSlash;
};

export const SITE_URL = import.meta.env.PUBLIC_SITE_URL || "https://raff-dev.github.io";
export const BASE_PATH = normalizeBasePath(import.meta.env.PUBLIC_BASE_PATH || "/goose");
export const SITE_NAME = "Goose";
export const REPO_URL = "https://github.com/Raff-dev/goose";
export const README_URL = `${REPO_URL}#readme`;
export const PYPI_URL = "https://pypi.org/project/llm-goose/";
export const NPM_URL = "https://www.npmjs.com/package/@llm-goose/dashboard-cli";
