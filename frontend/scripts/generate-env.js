// frontend/scripts/generate-env.js
// Generates env.js at build time so the static site knows the backend URL.
// Vercel: set BACKEND_URL in Project Settings -> Environment Variables
//         to your Render/Railway backend URL, e.g.
//         https://your-backend.onrender.com
// Local dev: if BACKEND_URL is not set, falls back to http://127.0.0.1:8000
//            so nothing breaks when running `npm run dev`.

const fs = require("fs");
const path = require("path");

const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";

const contents =
  "// AUTO-GENERATED at build time by scripts/generate-env.js — do not edit by hand.\n" +
  "window.__ENV__ = {\n" +
  '  BACKEND_URL: "' + backendUrl + '"\n' +
  "};\n";

fs.writeFileSync(path.join(__dirname, "..", "env.js"), contents);

console.log("Generated env.js with BACKEND_URL =", backendUrl);
