"use strict";

const state = { scenario: null, profiles: {}, flags: {} };

function optionButton(label, pressed, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "option";
  button.textContent = label;
  button.setAttribute("aria-pressed", String(pressed));
  button.addEventListener("click", onClick);
  return button;
}

function renderScenarios(scenarios) {
  const box = document.getElementById("scenarios");
  box.replaceChildren();
  if (scenarios.length === 0) {
    const empty = document.createElement("div");
    empty.className = "dim";
    empty.textContent = "no scenarios found";
    box.append(empty);
  }
  for (const { id, kind } of scenarios) {
    const mark = id === state.scenario ? "(*)" : "( )";
    box.append(optionButton(`${mark} ${id.padEnd(9)} ${kind}`, id === state.scenario, () => {
      state.scenario = id;
      renderScenarios(scenarios);
    }));
  }
  setText("scenario-name", state.scenario);
  document.getElementById("run").disabled = state.scenario === null;
}

function profileName() {
  const matches = ([, flags]) =>
    Object.keys(state.flags).every((key) => flags[key] === state.flags[key]);
  const match = Object.entries(state.profiles).find(matches);
  return match ? match[0] : "custom";
}

function renderLayers() {
  const box = document.getElementById("layers");
  box.replaceChildren();
  for (const [key, on] of Object.entries(state.flags)) {
    const label = `${on ? "[x]" : "[ ]"} ${key.replaceAll("_", " ")}`;
    box.append(optionButton(label, on, () => {
      state.flags[key] = !on;
      renderLayers();
    }));
  }
  const values = Object.values(state.flags);
  setText("profile", profileName());
  setText("layer-count", `${values.filter(Boolean).length}/${values.length}`);
}

function useProfile(name) {
  state.flags = { ...state.profiles[name] };
  renderLayers();
}

function span(className, text) {
  const element = document.createElement("span");
  element.className = className;
  element.textContent = text;
  return element;
}

function elapsed(startMs, timestamp) {
  const seconds = (Date.parse(timestamp) - startMs) / 1000;
  const minutes = Math.floor(seconds / 60);
  const rest = (seconds - minutes * 60).toFixed(1).padStart(4, "0");
  return `${String(minutes).padStart(2, "0")}:${rest}`;
}

// A defense event becomes a note under the line it acted on, as the UI spec describes.
function appendEvent(log, event, startMs) {
  if (event.event_type === "defense") {
    const note = document.createElement("div");
    note.className = "note";
    note.textContent = `└ ${event.defense}: ${event.content}`;
    log.append(note);
    return;
  }
  const line = document.createElement("div");
  line.className = "line";
  line.append(
    span("time", elapsed(startMs, event.timestamp)),
    span("agent", event.agent),
    span("event", event.event_type),
    span("", event.content),
  );
  log.append(line);
}

function showResult(text, className) {
  const result = document.getElementById("result");
  result.textContent = text;
  result.className = `result ${className}`;
  result.hidden = false;
}

function clearEvents(log) {
  log.replaceChildren(log.firstElementChild);
  log.hidden = true;
  document.getElementById("empty").hidden = false;
  document.getElementById("result").hidden = true;
}

function streamEvents(runId) {
  const log = document.getElementById("log");
  const source = new EventSource(`/runs/${encodeURIComponent(runId)}/events`);
  let startMs = null;
  source.onmessage = (message) => {
    const event = JSON.parse(message.data);
    startMs ??= Date.parse(event.timestamp);
    log.hidden = false;
    document.getElementById("empty").hidden = true;
    appendEvent(log, event, startMs);
  };
  source.addEventListener("result", (message) => {
    const { attack_succeeded: succeeded, detail } = JSON.parse(message.data);
    const label = succeeded ? "ATTACK SUCCEEDED" : "ATTACK BLOCKED";
    showResult(`[ ${label} ] ${detail}`, succeeded ? "bad" : "ok");
    source.close();
  });
  source.onerror = () => {
    source.close();
    showResult("event stream closed before a result arrived", "dim");
  };
}

async function startRun() {
  clearEvents(document.getElementById("log"));
  const response = await fetch("/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scenario_id: state.scenario,
      defenses: state.flags,
      trials: Number(document.getElementById("trials").value),
    }),
  });
  if (!response.ok) {
    showResult(`run not started: POST /runs returned HTTP ${response.status}`, "bad");
    return;
  }
  const { run_id: runId } = await response.json();
  setText("run-id", runId);
  streamEvents(runId);
}

async function init() {
  document.getElementById("baseline").addEventListener("click", () => useProfile("baseline"));
  document.getElementById("all").addEventListener("click", () => useProfile("all"));
  document.getElementById("run").addEventListener("click", startRun);
  try {
    const [defenses, scenarios] = await Promise.all([
      getJson("/config/defenses"),
      getJson("/scenarios"),
      showRunSettings(),
    ]);
    state.profiles = defenses.profiles;
    useProfile(defenses.active_profile);
    renderScenarios(scenarios);
  } catch (error) {
    showResult(`api unavailable: ${error.message}`, "bad");
  }
}

init();
