const state = { vocal: null, beat: null, beatB: null, renders: [], timelineEvents: [] };
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
  const canImport = $("vocal-file").files.length > 0 && $("beat-file").files.length > 0 && $("beat-b-file").files.length > 0;
  $("import-btn").disabled = !canImport;
  $("render-btn").disabled = !(state.vocal && state.beat && state.beatB);
  updateTimelineActions();
}
function showTrack(which, file) {
  $(which + "-name").textContent = file.name;
  $(which + "-detail").textContent = (file.size / (1024 * 1024)).toFixed(2) + " MiB · audio selected";
  $(which + "-state").textContent = "Selected";
}
$("vocal-file").addEventListener("change", e => { if (e.target.files[0]) showTrack("vocal", e.target.files[0]); updateActions(); });
$("beat-file").addEventListener("change", e => { if (e.target.files[0]) showTrack("beat", e.target.files[0]); updateActions(); });
$("beat-b-file").addEventListener("change", e => { if (e.target.files[0]) showTrack("beat-b", e.target.files[0]); updateActions(); });
async function api(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "Request failed (" + response.status + ")");
  return payload;
}
$("import-btn").addEventListener("click", async () => {
  const button = $("import-btn");
  button.disabled = true; button.textContent = "Importing…"; showMessage("Validating WAV / MP3 files on this computer…");
  try {
    const body = new FormData();
    body.append("vocal", $("vocal-file").files[0]);
    body.append("beat", $("beat-file").files[0]);
    body.append("beat_b", $("beat-b-file").files[0]);
    const result = await api("/api/import", { method: "POST", body });
    state.vocal = result.vocal; state.beat = result.beat; state.beatB = result.beat_b;
    $("vocal-name").textContent = result.vocal.original_name;
    $("vocal-detail").textContent = metaText(result.vocal.analysis);
    $("vocal-state").textContent = "Imported";
    $("beat-name").textContent = result.beat.original_name;
    $("beat-detail").textContent = metaText(result.beat.analysis);
    $("beat-state").textContent = "Imported";
    $("beat-b-name").textContent = result.beat_b.original_name;
    $("beat-b-detail").textContent = metaText(result.beat_b.analysis);
    $("beat-b-state").textContent = "Imported";
    $("import-btn").innerHTML = "3 tracks imported <span>✓</span>";
    showMessage("Vocal and both beats imported and analyzed. Choose Beat A or B for each render.", "success");
    updateActions();
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    if (!state.vocal || !state.beat || !state.beatB) {
      button.disabled = !($("vocal-file").files.length && $("beat-file").files.length && $("beat-b-file").files.length);
      button.innerHTML = 'Import 3 tracks <span>↗</span>';
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
    vocal_file: state.vocal.file, beat_file: ($("render-beat-choice").value === "beat-b" ? state.beatB.file : state.beat.file),
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


let discoveredPlugins = [];
async function scanPlugins() {
  const button = $("scan-plugins-btn");
  const status = $("plugin-scan-status");
  if (button) { button.disabled = true; button.textContent = "Scanning…"; }
  try {
    const data = await api("/api/plugins");
    discoveredPlugins = Array.isArray(data.plugins) ? data.plugins : [];
    const select = $("timeline-effect");
    [...select.options].filter(option => option.value.startsWith("vst3::")).forEach(option => option.remove());
    discoveredPlugins.forEach(plugin => {
      const option = document.createElement("option");
      option.value = "vst3::" + plugin.path;
      option.textContent = "Plugin: " + plugin.name;
      select.append(option);
    });
    if (status) status.textContent = discoveredPlugins.length ? discoveredPlugins.length + " VST3 plugin(s) found. Choose one from the Effect list." : "No VST3 plugins found in the standard Windows VST3 folder. Install the plugin first, then scan again.";
  } catch (error) { if (status) status.textContent = "Plugin scan failed: " + error.message; }
  finally { if (button) { button.disabled = false; button.textContent = "Scan installed VST3 plugins"; } }
}
if ($("scan-plugins-btn")) $("scan-plugins-btn").addEventListener("click", scanPlugins);
function selectedTimelineTrack() {
  const id = $("timeline-track").value;
  return id === "beat-b" ? state.beatB : id === "beat" ? state.beat : state.vocal;
}
function timelineTrackId() {
  return $("timeline-track").value;
}
function updateTimelineActions() {
  const track = selectedTimelineTrack();
  const hasEvents = state.timelineEvents.some(event => event.track_id === timelineTrackId());
  const button = $("render-timeline-btn");
  if (button) button.disabled = !(track && hasEvents);
}
function showTimelineMessage(text, kind = "") {
  const el = $("timeline-message");
  el.hidden = !text;
  el.className = "message" + (kind ? " " + kind : "");
  el.textContent = text;
}
function renderTimelineEventList() {
  const host = $("timeline-events");
  host.innerHTML = "";
  const visible = state.timelineEvents.filter(event => event.track_id === timelineTrackId());
  if (!visible.length) {
    const empty = document.createElement("div"); empty.className = "empty-state";
    empty.textContent = "No effect segments for this track yet. Add one above.";
    host.append(empty);
  }
  visible.forEach(event => {
    const row = document.createElement("div"); row.className = "timeline-event";
    const description = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = event.effect_kind === "vst3" ? ("VST3 · " + (event.plugin_path || "plugin").split(/[\\/]/).pop().replace(/\.vst3$/i, "")) : ({builtin_telephone:"Telephone / radio",builtin_reverb:"Reverb",builtin_delay:"Delay / echo",builtin_eq:"EQ / filtered tone",builtin_compressor:"Compressor"}[event.effect_kind] || event.effect_kind);
    const detail = document.createElement("p");
    detail.textContent = event.start_seconds.toFixed(2) + "–" + event.end_seconds.toFixed(2) + " sec · wet " + Math.round(event.wet * 100) + "% · fades " + event.fade_in_seconds + "/" + event.fade_out_seconds + " sec";
    description.append(title, detail);
    const remove = document.createElement("button"); remove.className = "button button-secondary";
    remove.type = "button"; remove.textContent = "Remove";
    remove.addEventListener("click", () => {
      state.timelineEvents = state.timelineEvents.filter(item => item.event_id !== event.event_id);
      renderTimelineEventList(); updateTimelineActions();
    });
    row.append(description, remove); host.append(row);
  });
  updateTimelineActions();
}
$("event-wet").addEventListener("input", () => {
  $("event-wet-out").textContent = $("event-wet").value + "%";
});
$("timeline-track").addEventListener("change", () => {
  renderTimelineEventList();
  showTimelineMessage("");
});
$("add-event-btn").addEventListener("click", () => {
  const track = selectedTimelineTrack();
  if (!track) {
    showTimelineMessage("Import your vocal and beat first.", "error");
    return;
  }
  const start = Number($("event-start").value);
  const end = Number($("event-end").value);
  const wet = Number($("event-wet").value) / 100;
  const fadeIn = Number($("event-fade-in").value);
  const fadeOut = Number($("event-fade-out").value);
  const duration = Number(track.analysis.duration_seconds);
  if (![start, end, wet, fadeIn, fadeOut, duration].every(Number.isFinite) ||
      start < 0 || end <= start || end > duration + 0.0005 ||
      fadeIn < 0 || fadeOut < 0 || fadeIn + fadeOut > end - start) {
    showTimelineMessage("Check the timestamps and fades. End must be after start and within the selected track duration (" + duration.toFixed(2) + " sec).", "error");
    return;
  }
  const effectSelection = $("timeline-effect").value;
  const isVst3 = effectSelection.startsWith("vst3::");
  const effect = isVst3 ? "vst3" : effectSelection;
  const pluginPath = isVst3 ? effectSelection.slice(6) : null;
  let parameters = {};
  if (effect === "builtin_reverb") parameters = {room_size: 0.35, damping: 0.5, width: 1.0};
  if (effect === "builtin_delay") parameters = {delay_seconds: 0.28, feedback: 0.25};
  state.timelineEvents.push({
    event_id: timelineTrackId() + "-" + Date.now() + "-" + state.timelineEvents.length,
    track_id: timelineTrackId(), effect_kind: effect, plugin_path: pluginPath,
    start_seconds: start, end_seconds: end, wet,
    fade_in_seconds: fadeIn, fade_out_seconds: fadeOut,
    parameters, enabled: true, decision_source: "user"
  });
  renderTimelineEventList();
  showTimelineMessage("Segment added. You can add more effects, then render this track.", "success");
});
$("render-timeline-btn").addEventListener("click", async () => {
  const track = selectedTimelineTrack();
  const trackId = timelineTrackId();
  const events = state.timelineEvents.filter(event => event.track_id === trackId);
  if (!track || !events.length) return;
  const button = $("render-timeline-btn");
  button.disabled = true; button.textContent = "Rendering segment effects…";
  showTimelineMessage("Rendering effects locally on the selected track. Source audio remains unchanged.");
  const timeline = {
    version: 1, project_name: "VeryRare segment render",
    duration_seconds: Number(track.analysis.duration_seconds),
    events
  };
  try {
    const result = await api("/api/render-timeline", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({track_file: track.file, track_id: trackId, timeline_json: JSON.stringify(timeline)})
    });
    if (result.rendered !== true || !result.output_file) throw new Error("The engine did not confirm a successful render.");
    $("timeline-result-name").textContent = result.output_file + " · " + result.report.event_count + " event(s)";
    $("timeline-audio").src = result.audio_url;
    $("timeline-download").href = result.audio_url;
    $("timeline-download").download = result.output_file;
    $("timeline-result").hidden = false;
    showTimelineMessage("Segment render completed. Listen to it before using it in your final mix.", "success");
  } catch (error) {
    showTimelineMessage(error.message, "error");
  } finally {
    button.textContent = "Render selected track →";
    updateTimelineActions();
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
  resultBox.hidden = false; resultBox.textContent = "Asking the configured text planner. It receives your written brief, not the audio waveform; no audio is sent.";
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

async function loadPluginCatalog() {
  const host = $("plugin-catalog");
  const note = $("plugin-catalog-note");
  try {
    const data = await api("/api/plugin-catalog");
    host.innerHTML = "";
    data.plugins.forEach(plugin => {
      const card = document.createElement("article");
      card.className = "plugin-card";
      const top = document.createElement("div"); top.className = "plugin-card-top";
      const title = document.createElement("strong"); title.textContent = plugin.name;
      const size = document.createElement("span"); size.className = "plugin-size"; size.textContent = plugin.zip_mib.toFixed(2) + " MiB ZIP";
      top.append(title, size);
      const category = document.createElement("span"); category.className = "plugin-category"; category.textContent = plugin.category;
      const description = document.createElement("p"); description.textContent = plugin.purpose;
      const meta = document.createElement("p"); meta.className = "plugin-meta"; meta.textContent = plugin.vendor + " · " + plugin.format;
      const link = document.createElement("a"); link.className = "button button-secondary"; link.href = plugin.official_url;
      link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = "Official download page ↗";
      card.append(top, category, description, meta, link);
      host.append(card);
    });
    if (note) note.textContent = data.notice || "Download only from the official developer site. Installation and plugin loading are separate steps.";
  } catch (error) {
    host.textContent = "Could not load the plugin catalog: " + error.message;
  }
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
document.querySelectorAll(".workflow-step").forEach(step => {
  step.addEventListener("click", () => {
    document.querySelectorAll(".workflow-step").forEach(item => {
      const active = item === step;
      item.classList.toggle("current", active);
      if (active) item.setAttribute("aria-current", "step");
      else item.removeAttribute("aria-current");
    });
  });
});
const sections = {studio:"studio-section",effects:"effects-section",activity:"activity-section"};
document.querySelectorAll("[data-section]").forEach(button => button.addEventListener("click", () => {
  Object.entries(sections).forEach(([key, id]) => $(id).classList.toggle("hidden", key !== button.dataset.section));
  document.querySelectorAll("[data-section]").forEach(item => item.classList.toggle("active", item === button));
  $("crumb").textContent = ({studio:"Studio",effects:"Effects library",activity:"Render reports"}[button.dataset.section]);
  if (button.dataset.section === "effects") { loadCapabilities(); loadPluginCatalog(); }
  if (button.dataset.section === "activity") renderHistory();
  window.scrollTo({top:0, behavior:"smooth"});
}));
scanPlugins();
api("/api/health").then(data => {
  $("health-text").textContent = "Local engine connected";
  if (data.cloud_audio_upload !== false) $("health-text").textContent = "Check privacy status";
}).catch(() => { $("health-text").textContent = "Local engine unavailable"; });


// Local realtime audition. Files remain in this browser; no upload or source overwrite.
const livePreview = { context: null, source: null, objectUrls: {}, enabled: false, comparingDry: false, nodes: [] };
function liveStatus(message) { const el = $("live-preview-status"); if (el) el.textContent = message; }
function liveFile() {
  const which = $("live-preview-track")?.value || "vocal";
  return { which, file: $(which + "-file")?.files?.[0] || null };
}
function loadLivePreviewFile() {
  const {which, file} = liveFile();
  const audio = $("live-preview-audio");
  if (!audio) return;
  if (!file) {
    audio.removeAttribute("src"); audio.load();
    liveStatus("Choose a " + (which === "vocal" ? "vocal" : "beat") + " file above first.");
    $("live-preview-enable").disabled = true;
    return;
  }
  if (livePreview.objectUrls[which]) URL.revokeObjectURL(livePreview.objectUrls[which]);
  livePreview.objectUrls[which] = URL.createObjectURL(file);
  audio.src = livePreview.objectUrls[which]; audio.load();
  $("live-preview-enable").disabled = false;
  liveStatus("Local preview: " + file.name + ". Press play, then adjust controls while it plays.");
  if (livePreview.enabled && !livePreview.comparingDry) rebuildLiveGraph();
}
function liveNode(node) { livePreview.nodes.push(node); return node; }
function makeImpulse(context, seconds = 2.8, decay = 2.4) {
  const length = Math.max(1, Math.floor(context.sampleRate * seconds));
  const impulse = context.createBuffer(2, length, context.sampleRate);
  for (let channel = 0; channel < 2; channel++) {
    const data = impulse.getChannelData(channel);
    for (let i = 0; i < length; i++) data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, decay);
  }
  return impulse;
}
function disconnectLiveGraph() {
  if (livePreview.source) { try { livePreview.source.disconnect(); } catch (_) {} }
  livePreview.nodes.forEach(node => { try { node.disconnect(); } catch (_) {} });
  livePreview.nodes = [];
}
function rebuildLiveGraph() {
  if (!livePreview.context || !livePreview.source || !livePreview.enabled || livePreview.comparingDry) return;
  const ctx = livePreview.context;
  disconnectLiveGraph();
  const preGain = liveNode(ctx.createGain());
  preGain.gain.value = Math.pow(10, Number($("live-level").value) / 20);
  const highpass = liveNode(ctx.createBiquadFilter());
  highpass.type = "highpass"; highpass.frequency.value = Number($("highpass")?.value || 80);
  const presence = liveNode(ctx.createBiquadFilter());
  presence.type = "peaking"; presence.frequency.value = 3200; presence.Q.value = 0.8;
  presence.gain.value = Number($("presence")?.value || 0);
  const comp = liveNode(ctx.createDynamicsCompressor());
  comp.threshold.value = Number($("threshold")?.value || -18);
  comp.ratio.value = Number($("compression")?.value || 2);
  comp.knee.value = 18; comp.attack.value = 0.012; comp.release.value = 0.18;
  const dry = liveNode(ctx.createGain());
  const wet = liveNode(ctx.createGain());
  const master = liveNode(ctx.createGain());
  const limiter = liveNode(ctx.createDynamicsCompressor());
  limiter.threshold.value = -3; limiter.knee.value = 2; limiter.ratio.value = 12;
  limiter.attack.value = 0.003; limiter.release.value = 0.12;
  const amount = Number($("live-wet").value) / 100;
  const effect = $("live-preview-effect").value;
  dry.gain.value = effect === "clean" ? 1 : Math.cos(amount * Math.PI / 2);
  wet.gain.value = effect === "clean" ? 0 : Math.sin(amount * Math.PI / 2);
  livePreview.source.connect(preGain);
  preGain.connect(highpass); highpass.connect(presence); presence.connect(comp);
  comp.connect(dry); dry.connect(master);
  if (effect === "telephone") {
    const band = liveNode(ctx.createBiquadFilter());
    band.type = "bandpass"; band.frequency.value = 1550; band.Q.value = 0.65;
    const shaper = liveNode(ctx.createWaveShaper());
    const curve = new Float32Array(2048);
    for (let i = 0; i < curve.length; i++) { const x = i * 2 / (curve.length - 1) - 1; curve[i] = Math.tanh(2.2 * x) / Math.tanh(2.2); }
    shaper.curve = curve; shaper.oversample = "2x";
    const tone = liveNode(ctx.createBiquadFilter()); tone.type = "lowpass"; tone.frequency.value = Number($("live-tone").value);
    comp.connect(band); band.connect(shaper); shaper.connect(tone); tone.connect(wet);
  } else if (effect === "reverb" || effect === "dreamcore") {
    const tail = Number($("live-tail").value);
    const convolver = liveNode(ctx.createConvolver());
    convolver.buffer = makeImpulse(ctx, tail, effect === "dreamcore" ? 1.8 : 2.8);
    if (effect === "dreamcore") {
      const lowpass = liveNode(ctx.createBiquadFilter()); lowpass.type = "lowpass"; lowpass.frequency.value = Number($("live-tone").value);
      comp.connect(lowpass); lowpass.connect(convolver);
    } else comp.connect(convolver);
    convolver.connect(wet);
  }
  if (effect === "delay" || effect === "dreamcore") {
    const delay = liveNode(ctx.createDelay(1.5));
    delay.delayTime.value = Number($("delay-time")?.value || 260) / 1000;
    const feedback = liveNode(ctx.createGain());
    feedback.gain.value = Math.min(0.65, Number($("live-feedback").value) / 100);
    comp.connect(delay); delay.connect(feedback); feedback.connect(delay); delay.connect(wet);
  } else if (effect !== "telephone" && effect !== "reverb" && effect !== "dreamcore") {
    comp.connect(wet);
    if (effect === "clean") wet.gain.value = 0;
  }
  wet.connect(master);
  master.connect(limiter); limiter.connect(ctx.destination);
}
async function enableLivePreview() {
  const {file} = liveFile();
  if (!file) { liveStatus("Choose a vocal or beat file above first."); return; }
  const audio = $("live-preview-audio");
  try {
    if (!livePreview.context) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) throw new Error("This browser does not support Web Audio.");
      livePreview.context = new AudioContextClass();
      livePreview.source = livePreview.context.createMediaElementSource(audio);
    }
    await livePreview.context.resume();
    livePreview.enabled = true; livePreview.comparingDry = false;
    rebuildLiveGraph();
    $("live-preview-bypass").disabled = false;
    $("live-preview-ab").disabled = false;
    $("live-preview-enable").textContent = "Realtime effects enabled ✓";
    $("live-preview-ab").textContent = "Compare A/B (dry)";
    liveStatus("Effects active. Use Compare A/B to switch instantly between the source and processed sound.");
  } catch (error) { liveStatus("Realtime preview error: " + error.message); }
}
function bypassLivePreview() {
  if (!livePreview.context || !livePreview.source) return;
  livePreview.enabled = false; livePreview.comparingDry = false;
  disconnectLiveGraph();
  livePreview.source.connect(livePreview.context.destination);
  $("live-preview-enable").textContent = "Enable realtime effects";
  $("live-preview-bypass").disabled = true;
  $("live-preview-ab").disabled = true;
  $("live-preview-ab").textContent = "Compare A/B";
  liveStatus("Effects bypassed. Enable realtime effects to return to processed playback.");
}
function toggleLiveAB() {
  if (!livePreview.enabled || !livePreview.source) return;
  livePreview.comparingDry = !livePreview.comparingDry;
  disconnectLiveGraph();
  if (livePreview.comparingDry) {
    livePreview.source.connect(livePreview.context.destination);
    $("live-preview-ab").textContent = "A/B: DRY (switch to wet)";
    liveStatus("A/B comparison: dry source. Press the same button to hear the processed version.");
  } else {
    rebuildLiveGraph();
    $("live-preview-ab").textContent = "A/B: WET (switch to dry)";
    liveStatus("A/B comparison: processed sound.");
  }
}
if ($("live-preview-enable")) {
  $("live-preview-enable").addEventListener("click", enableLivePreview);
  $("live-preview-bypass").addEventListener("click", bypassLivePreview);
  $("live-preview-ab").addEventListener("click", toggleLiveAB);
  $("live-preview-track").addEventListener("change", () => {
    if (livePreview.enabled) bypassLivePreview();
    loadLivePreviewFile();
  });
  $("live-preview-effect").addEventListener("change", () => { if (livePreview.enabled && !livePreview.comparingDry) rebuildLiveGraph(); });
  const liveRanges = [
    ["live-wet", "live-wet-out", v => v + "%"],
    ["live-level", "live-level-out", v => v + " dB"],
    ["live-tail", "live-tail-out", v => Number(v).toFixed(1) + " s"],
    ["live-feedback", "live-feedback-out", v => v + "%"],
    ["live-tone", "live-tone-out", v => (Number(v) / 1000).toFixed(1) + " kHz"]
  ];
  liveRanges.forEach(([inputId, outputId, format]) => {
    $(inputId).addEventListener("input", () => {
      $(outputId).textContent = format($(inputId).value);
      if (livePreview.enabled && !livePreview.comparingDry) rebuildLiveGraph();
    });
    $(outputId).textContent = format($(inputId).value);
  });
  ["highpass", "presence", "compression", "threshold", "delay-time"].forEach(id => {
    $(id)?.addEventListener("input", () => { if (livePreview.enabled && !livePreview.comparingDry) rebuildLiveGraph(); });
  });
  ["vocal-file", "beat-file"].forEach(id => $(id)?.addEventListener("change", () => {
    const current = $("live-preview-track").value;
    if (id === current + "-file") loadLivePreviewFile();
  }));
  window.addEventListener("beforeunload", () => Object.values(livePreview.objectUrls).forEach(url => URL.revokeObjectURL(url)));
  loadLivePreviewFile();
}
