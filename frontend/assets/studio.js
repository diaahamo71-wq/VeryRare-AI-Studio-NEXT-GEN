const state = { vocal: null, beat: null, renders: [] };
const $ = (id) => document.getElementById(id);
const fields = {
  "vocal-gain": ["vocal-gain-out", v => Number(v).toFixed(1) + " dB"],
  "beat-gain": ["beat-gain-out", v => Number(v).toFixed(1) + " dB"],
  highpass: ["highpass-out", v => v + " Hz"],
  presence: ["presence-out", v => (Number(v) > 0 ? "+" : "") + Number(v).toFixed(1) + " dB"],
  compression: ["compression-out", v => Number(v).toFixed(2).replace(/0$/, "") + ":1"],
  threshold: ["threshold-out", v => v + " dB"],
  reverb: ["reverb-out", v => v + "%"],
  delay: ["delay-out", v => v + "%"],
  "delay-time": ["delay-time-out", v => v + " ms"],
  ceiling: ["ceiling-out", v => Number(v).toFixed(1) + " dBFS"]
};
Object.entries(fields).forEach(([inputId, [outputId, format]]) => {
  const input = $(inputId);
  const update = () => { $(outputId).textContent = format(input.value); };
  input.addEventListener("input", update);
  update();
});
function showMessage(text, kind = "") {
  const el = $("message");
  el.hidden = !text;
  el.className = "message" + (kind ? " " + kind : "");
  el.textContent = text;
}
function updateActions() {
  const canImport = $("vocal-file").files.length > 0 && $("beat-file").files.length > 0;
  $("import-btn").disabled = !canImport;
  $("render-btn").disabled = !(state.vocal && state.beat);
  $("smart-mix-btn").disabled = !(state.vocal && state.beat);
  $("ai-engineer-btn").disabled = !(state.vocal && state.beat);
}
function showTrack(which, file) {
  $(which + "-name").textContent = file.name;
  $(which + "-detail").textContent = (file.size / (1024 * 1024)).toFixed(2) + " MiB · WAV selected";
  $(which + "-state").textContent = "Selected";
}
$("vocal-file").addEventListener("change", e => { if (e.target.files[0]) showTrack("vocal", e.target.files[0]); updateActions(); });
$("beat-file").addEventListener("change", e => { if (e.target.files[0]) showTrack("beat", e.target.files[0]); updateActions(); });
async function api(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "Request failed (" + response.status + ")");
  return payload;
}
$("import-btn").addEventListener("click", async () => {
  const button = $("import-btn");
  button.disabled = true; button.textContent = "Importing…"; showMessage("Validating both WAV files on this computer…");
  try {
    const body = new FormData();
    body.append("vocal", $("vocal-file").files[0]);
    body.append("beat", $("beat-file").files[0]);
    const result = await api("/api/import", { method: "POST", body });
    state.vocal = result.vocal; state.beat = result.beat;
    $("vocal-name").textContent = result.vocal.original_name;
    $("vocal-detail").textContent = metaText(result.vocal.analysis);
    $("vocal-state").textContent = "Imported";
    $("beat-name").textContent = result.beat.original_name;
    $("beat-detail").textContent = metaText(result.beat.analysis);
    $("beat-state").textContent = "Imported";
    $("import-btn").innerHTML = "Tracks imported <span>✓</span>";
    showMessage("Both tracks imported and analyzed successfully. You can now render a mix.", "success");
    updateActions();
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    if (!state.vocal || !state.beat) {
      button.disabled = !($("vocal-file").files.length && $("beat-file").files.length);
      button.innerHTML = 'Import tracks <span>↗</span>';
    }
  }
});
function metaText(a) {
  return a.duration_seconds + " sec · " + (a.sample_rate_hz / 1000).toFixed(1) + " kHz · " + a.channels + " ch";
}
$("render-btn").addEventListener("click", async () => {
  const button = $("render-btn");
  button.disabled = true; button.innerHTML = '<span class="button-star">◌</span> Rendering…';
  showMessage("Processing locally. Longer WAV files may take a little time.");
  const request = {
    vocal_file: state.vocal.file, beat_file: state.beat.file,
    vocal_gain_db: Number($("vocal-gain").value),
    beat_gain_db: Number($("beat-gain").value),
    highpass_hz: Number($("highpass").value),
    presence_db: Number($("presence").value),
    compression_ratio: Number($("compression").value),
    compression_threshold_db: Number($("threshold").value),
    reverb_mix: Number($("reverb").value) / 100,
    delay_mix: Number($("delay").value) / 100,
    delay_ms: Number($("delay-time").value),
    master_peak_dbfs: Number($("ceiling").value)
  };
  try {
    const result = await api("/api/mix", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(request)});
    if (result.rendered !== true || !result.output_file) throw new Error("The engine did not confirm a successful render.");
    const output = result.report.output;
    $("result-name").textContent = result.output_file;
    $("result-meta").textContent = output.duration_seconds + " sec · " + output.sample_rate_hz + " Hz · 24-bit PCM WAV";
    $("reference-audio").src = result.reference_url;
    $("result-audio").src = result.audio_url;
    $("download-link").href = result.audio_url;
    $("download-link").download = result.output_file;
    $("result-panel").hidden = false;
    $("report-grid").innerHTML = "";
    const metrics = [
      ["Output peak", output.peak_dbfs + " dBFS"],
      ["Output RMS", output.rms_dbfs + " dBFS"],
      ["Duration", output.duration_seconds + " s"],
      ["Clipped samples", output.clipped_sample_count]
    ];
    metrics.forEach(([label, value]) => {
      const card = document.createElement("div"); card.className = "report-metric";
      const caption = document.createElement("span"); caption.textContent = label;
      const strong = document.createElement("strong"); strong.textContent = value;
      card.append(caption, strong); $("report-grid").append(card);
    });
    const item = {name: result.output_file, url: result.audio_url, date: new Date().toLocaleString(), peak: output.peak_dbfs, rms: output.rms_dbfs};
    state.renders.unshift(item); renderHistory();
    showMessage("Render complete. Technical checks passed; please listen and compare before release.", "success");
    $("result-panel").scrollIntoView({behavior: "smooth", block: "start"});
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    button.disabled = false; button.innerHTML = '<span class="button-star">✦</span> Render mix <span class="button-arrow">→</span>';
    updateActions();
  }
});

$("smart-mix-btn").addEventListener("click", async () => {
  if (!state.vocal || !state.beat) return;
  const button = $("smart-mix-btn");
  button.disabled = true;
  button.textContent = "Analyzing levels…";
  showMessage("Measuring both WAV files locally and building a conservative, editable starting point.");
  try {
    const result = await api("/api/smart-mix", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        vocal_file: state.vocal.file,
        beat_file: state.beat.file,
        brief: $("production-brief").value.trim()
      })
    });
    const s = result.settings || {};
    const mapping = {
      "vocal-gain": s.vocal_gain_db,
      "beat-gain": s.instrumental_gain_db,
      highpass: s.vocal_highpass_hz,
      presence: s.vocal_presence_db,
      compression: s.compression_ratio,
      threshold: s.compression_threshold_db,
      reverb: Math.round((s.reverb_mix || 0) * 100),
      delay: Math.round((s.delay_mix || 0) * 100),
      "delay-time": s.delay_ms,
      ceiling: s.master_peak_dbfs
    };
    Object.entries(mapping).forEach(([id, value]) => {
      if (value === undefined || value === null || !$(id)) return;
      $(id).value = String(value);
      $(id).dispatchEvent(new Event("input", {bubbles: true}));
    });
    const details = (result.reasons || []).join(" ");
    showMessage("Local smart starting point applied to the mix controls. " + details + " Listen and adjust before exporting.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    button.innerHTML = 'Suggest local mix settings <span>↗</span>';
    updateActions();
  }
});

$("ai-engineer-btn").addEventListener("click", async () => {
  if (!state.vocal || !state.beat) return;
  const button = $("ai-engineer-btn");
  button.disabled = true;
  button.textContent = "AI analyzing and planning…";
  showMessage("The local pretrained AI is reading your brief and objective measurements. Audio stays on this computer.");
  try {
    const result = await api("/api/ai-engineer", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        vocal_file: state.vocal.file,
        beat_file: state.beat.file,
        brief: $("production-brief").value.trim()
      })
    });
    const s = result.settings || {};
    const mapping = {
      "vocal-gain": s.vocal_gain_db,
      "beat-gain": s.instrumental_gain_db,
      highpass: s.vocal_highpass_hz,
      presence: s.vocal_presence_db,
      compression: s.compression_ratio,
      threshold: s.compression_threshold_db,
      reverb: Math.round(s.reverb_mix * 100),
      delay: Math.round(s.delay_mix * 100),
      "delay-time": s.delay_ms,
      ceiling: s.master_peak_dbfs
    };
    Object.entries(mapping).forEach(([id, value]) => {
      if (value === undefined || value === null || !$(id)) return;
      $(id).value = String(value);
      $(id).dispatchEvent(new Event("input", {bubbles: true}));
    });
    const decisions = (result.decisions || []).join(" ");
    const warnings = (result.warnings || []).join(" ");
    showMessage("AI plan ready (" + result.model + "). " + result.summary + " " + decisions + (warnings ? " Notes: " + warnings : "") + " Starting the actual local DSP render now.", "success");
    button.textContent = "AI plan ready · Rendering…";
    $("render-btn").click();
  } catch (error) {
    showMessage(error.message + " The app did not silently substitute random or heuristic settings.", "error");
  } finally {
    button.innerHTML = 'AI Engineer · Plan and mix <span>✦</span>';
    updateActions();
  }
});

$("production-brief").addEventListener("input", () => {
  $("plan-btn").disabled = $("production-brief").value.trim().length < 3;
});
$("plan-btn").disabled = true;
$("plan-btn").addEventListener("click", async () => {
  const prompt = $("production-brief").value.trim();
  if (prompt.length < 3) return;
  const button = $("plan-btn");
  const resultBox = $("plan-result");
  button.disabled = true; button.textContent = "Planning…";
  resultBox.hidden = false; resultBox.textContent = "Asking the configured text planner. Audio files are not sent.";
  try {
    const response = await api("/api/plan", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({prompt, allow_cloud_fallback: $("allow-cloud").checked})
    });
    const plan = response.plan || {};
    resultBox.innerHTML = "";
    const title = document.createElement("h4");
    title.textContent = plan.summary || "Effect plan";
    resultBox.append(title);
    const agent = document.createElement("p");
    agent.textContent = "Planner: " + (plan.agent || "unknown") + " · Execution: not run";
    resultBox.append(agent);
    (Array.isArray(plan.operations) ? plan.operations : []).forEach((operation, index) => {
      const item = document.createElement("div"); item.className = "plan-operation";
      const name = document.createElement("strong");
      name.textContent = (index + 1) + ". " + (operation.capability || "Suggested operation") + " · " + (operation.track || "track");
      const reason = document.createElement("p");
      reason.textContent = (operation.reason || operation.parameter_intent || "No rationale provided.") + (operation.plugin_name_or_id ? " · Plugin: " + operation.plugin_name_or_id : "");
      item.append(name, reason); resultBox.append(item);
    });
    if (Array.isArray(plan.needs_user_input) && plan.needs_user_input.length) {
      const needs = document.createElement("p"); needs.className = "plan-warning";
      needs.textContent = "Needs your input: " + plan.needs_user_input.join("; ");
      resultBox.append(needs);
    }
    if (plan.error) {
      const error = document.createElement("p"); error.className = "plan-warning"; error.textContent = plan.error; resultBox.append(error);
    }
    const note = document.createElement("p"); note.textContent = response.notice || "Plan is advisory only."; resultBox.append(note);
    showMessage(response.planned ? "Advisory effect plan created. Review it before applying anything." : "Local planner unavailable; check that Ollama is running and the configured model is installed.", response.planned ? "success" : "");
  } catch (error) {
    resultBox.textContent = error.message;
    showMessage(error.message, "error");
  } finally {
    button.disabled = $("production-brief").value.trim().length < 3;
    button.innerHTML = 'Create effect plan <span>✧</span>';
  }
});

function renderHistory() {
  const host = $("activity-list"); host.innerHTML = "";
  if (!state.renders.length) { host.innerHTML = '<div class="empty-state">No renders yet. Your first mix will show up here.</div>'; return; }
  state.renders.forEach(item => {
    const card = document.createElement("div"); card.className = "activity-card";
    const icon = document.createElement("div"); icon.className = "result-file-icon"; icon.textContent = "♫";
    const info = document.createElement("div"); info.className = "activity-info";
    const name = document.createElement("strong"); name.textContent = item.name;
    const detail = document.createElement("p"); detail.textContent = item.date + " · peak " + item.peak + " dBFS · RMS " + item.rms + " dBFS";
    info.append(name, detail);
    const link = document.createElement("a"); link.className = "button button-secondary"; link.href = item.url; link.download = item.name; link.textContent = "Download ↓";
    card.append(icon, info, link); host.append(card);
  });
}
async function loadCapabilities() {
  try {
    const data = await api("/api/capabilities");
    const host = $("capabilities"); host.innerHTML = "";
    data.capabilities.forEach(item => {
      const card = document.createElement("article"); card.className = "capability-card";
      const symbol = document.createElement("div"); symbol.className = "capability-symbol"; symbol.textContent = ({equalization:"⌁",dynamics:"◒",spatial:"◌",mixing:"↔",pitch:"♬","vocal layers":"♬",restoration:"⌕",mastering:"◉"}[item.category] || "✧");
      const content = document.createElement("div"); content.className = "capability-content";
      const title = document.createElement("strong"); title.textContent = item.name;
      const description = document.createElement("p"); description.textContent = item.purpose + " " + item.safety_notes;
      content.append(title, description);
      const badge = document.createElement("span"); badge.className = "capability-status status-" + item.status;
      badge.textContent = ({implemented_builtin:"Built-in DSP",external_plugin_required:"Needs external plugin",planned:"Planned"}[item.status] || item.status);
      card.append(symbol, content, badge); host.append(card);
    });
  } catch (error) { $("capabilities").textContent = "Could not load the effects inventory: " + error.message; }
}
const sections = {studio:"studio-section",effects:"effects-section",activity:"activity-section"};
document.querySelectorAll("[data-section]").forEach(button => button.addEventListener("click", () => {
  Object.entries(sections).forEach(([key, id]) => $(id).classList.toggle("hidden", key !== button.dataset.section));
  document.querySelectorAll("[data-section]").forEach(item => item.classList.toggle("active", item === button));
  $("crumb").textContent = ({studio:"Studio",effects:"Effects library",activity:"Render reports"}[button.dataset.section]);
  if (button.dataset.section === "effects") loadCapabilities();
  if (button.dataset.section === "activity") renderHistory();
  window.scrollTo({top:0, behavior:"smooth"});
}));
api("/api/health").then(data => {
  $("health-text").textContent = "Local engine connected";
  if (data.cloud_audio_upload !== false) $("health-text").textContent = "Check privacy status";
}).catch(() => { $("health-text").textContent = "Local engine unavailable"; });
