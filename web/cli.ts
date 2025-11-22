#!/usr/bin/env node

import { existsSync, readFileSync } from 'node:fs';
import http from 'node:http';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const port = Number(process.env.GOOSE_DASHBOARD_PORT ?? 8001);
const distDir = resolve(__dirname, 'client');

if (!existsSync(distDir)) {
  console.error('Goose dashboard assets not found. Make sure `npm run build` has been run before publishing.');
  process.exit(1);
}

const mimeTypes: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml; charset=utf-8',
  '.ico': 'image/x-icon',
};

const server = http.createServer((req, res) => {
  const url = req.url || '/';
  const safePath = url.split('?')[0].split('#')[0];
  const filePath = safePath === '/' ? join(distDir, 'index.html') : join(distDir, safePath.replace(/^\//, ''));

  let contentPath = filePath;
  if (!existsSync(contentPath)) {
    contentPath = join(distDir, 'index.html');
  }

  try {
    const data = readFileSync(contentPath);
    const ext = extname(contentPath).toLowerCase();
    const contentType = mimeTypes[ext] ?? 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  } catch (err) {
    res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Internal server error');
  }
});

server.listen(port, () => {
  console.log(`Goose dashboard running at http://localhost:${port}/`);
  if (process.env.GOOSE_API_URL) {
    console.log(`Using Goose API at ${process.env.GOOSE_API_URL}`);
  }
});
