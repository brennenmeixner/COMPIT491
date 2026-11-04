"use strict";

// API values are always rendered with textContent, never parsed as markup.
function setText(id, value) {
  document.getElementById(id).textContent = value ?? "-";
}

async function getJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${path} returned HTTP ${response.status}`);
  }
  return response.json();
}

async function showRunSettings() {
  const results = await getJson("/results");
  setText("model", results.model ?? "unset");
  setText("seed", results.seed);
  return results;
}
