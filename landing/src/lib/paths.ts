import { BASE_PATH } from "../config.ts";

export const withBase = (path = "") => {
  if (!path || path === "/") {
    return BASE_PATH ? `${BASE_PATH}/` : "/";
  }

  if (/^https?:\/\//.test(path)) {
    return path;
  }

  if (path.startsWith("#")) {
    return BASE_PATH ? `${BASE_PATH}/${path}` : path;
  }

  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  return BASE_PATH ? `${BASE_PATH}/${normalizedPath}` : `/${normalizedPath}`;
};
