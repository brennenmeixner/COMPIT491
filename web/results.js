"use strict";

const CONFIGURATIONS = ["baseline", "input", "output", "tools", "memory", "sandbox", "all"];
const ATTACK_TYPES = [
  "prompt injection",
  "unauthorized tool use",
  "memory poisoning",
  "data leakage",
];
const TASK_COLUMNS = [
  ["completed", "completed (higher)"],
  ["false_blocks", "false blocks (lower)"],
  ["added_latency", "added latency (s)"],
];

function cell(text, className = "") {
  const element = document.createElement("span");
  element.className = className;
  element.textContent = text;
  return element;
}

function valueCell(value) {
  return value === undefined ? cell("-", "num cell-empty") : cell(String(value), "num");
}

function renderAttackGrid(attackSuccess) {
  const grid = document.getElementById("attack-grid");
  grid.replaceChildren(
    cell("attack", "head"),
    ...CONFIGURATIONS.map((name) => cell(name, "head num")),
  );
  for (const attack of ATTACK_TYPES) {
    grid.append(cell(attack));
    for (const configuration of CONFIGURATIONS) {
      grid.append(valueCell(attackSuccess[attack]?.[configuration]));
    }
  }
}

function renderTaskGrid(normalTasks) {
  const grid = document.getElementById("task-grid");
  grid.replaceChildren(
    cell("configuration", "head"),
    ...TASK_COLUMNS.map(([, label]) => cell(label, "head num")),
  );
  for (const configuration of CONFIGURATIONS) {
    grid.append(cell(configuration));
    for (const [key] of TASK_COLUMNS) {
      grid.append(valueCell(normalTasks[configuration]?.[key]));
    }
  }
}

async function init() {
  // The grids draw with "-" first, so a failed request can never look like data.
  renderAttackGrid({});
  renderTaskGrid({});
  try {
    const results = await showRunSettings();
    renderAttackGrid(results.attack_success);
    renderTaskGrid(results.normal_tasks);
    setText("scenario-count", results.scenarios);
    setText("trial-count", results.trials_per_scenario);
  } catch (error) {
    setText("note", `api unavailable: ${error.message}`);
  }
}

init();
