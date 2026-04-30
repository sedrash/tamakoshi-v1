const API_BASE = `${window.location.origin}/api`;

const state = {
  characters: [],
  actions: [],
  selectedId: null,
  selected: null,
  loading: false,
};

const els = {
  apiStatus: document.querySelector("#apiStatus"),
  createForm: document.querySelector("#createForm"),
  nameInput: document.querySelector("#nameInput"),
  promptInput: document.querySelector("#promptInput"),
  refreshButton: document.querySelector("#refreshButton"),
  characterList: document.querySelector("#characterList"),
  emptyState: document.querySelector("#emptyState"),
  dashboard: document.querySelector("#dashboard"),
  characterName: document.querySelector("#characterName"),
  characterPrompt: document.querySelector("#characterPrompt"),
  tickButton: document.querySelector("#tickButton"),
  multiTickButton: document.querySelector("#multiTickButton"),
  deleteButton: document.querySelector("#deleteButton"),
  logsButton: document.querySelector("#logsButton"),
  petVisual: document.querySelector("#petVisual"),
  lifeBadge: document.querySelector("#lifeBadge"),
  feelingText: document.querySelector("#feelingText"),
  lastActionText: document.querySelector("#lastActionText"),
  moneyValue: document.querySelector("#moneyValue"),
  foodValue: document.querySelector("#foodValue"),
  ticksValue: document.querySelector("#ticksValue"),
  updatedAt: document.querySelector("#updatedAt"),
  statsGrid: document.querySelector("#statsGrid"),
  logList: document.querySelector("#logList"),
  actionsList: document.querySelector("#actionsList"),
  toast: document.querySelector("#toast"),
};

const stats = [
  ["hp", "Vie"],
  ["hunger", "Faim"],
  ["energy", "Energie"],
  ["hygiene", "Hygiene"],
  ["mental", "Mental"],
  ["entertainment", "Loisir"],
];

function apiUrl(path) {
  return `${API_BASE}${path}`;
}

async function request(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Erreur ${response.status}`;
    try {
      const body = await response.json();
      message = body.error || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.remove("hidden");
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    els.toast.classList.add("hidden");
  }, 3200);
}

function formatDate(value) {
  if (!value) {
    return "";
  }
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function setLoading(isLoading) {
  state.loading = isLoading;
  els.tickButton.disabled = isLoading;
  els.multiTickButton.disabled = isLoading;
  els.refreshButton.disabled = isLoading;
  els.logsButton.disabled = isLoading;
  els.createForm.querySelector("button").disabled = isLoading;
}

function updateApiStatus(ok) {
  els.apiStatus.textContent = ok ? "API connectee" : "API hors ligne";
  els.apiStatus.style.color = ok ? "var(--green-dark)" : "var(--red)";
}

function renderCharacters() {
  if (state.characters.length === 0) {
    els.characterList.innerHTML = '<p class="muted">Aucun personnage.</p>';
    return;
  }

  els.characterList.innerHTML = state.characters
    .map((character) => {
      const active = character.id === state.selectedId ? " active" : "";
      const status = character.isAlive ? character.feeling : character.deathReason || "Mort";
      return `
        <button class="character-card${active}" type="button" data-id="${character.id}">
          <strong>${escapeHtml(character.name)}</strong>
          <span>${escapeHtml(status || "")}</span>
        </button>
      `;
    })
    .join("");
}

function renderStats(character) {
  els.statsGrid.innerHTML = stats
    .map(([key, label]) => {
      const value = Math.max(0, Math.min(Number(character[key] || 0), 100));
      const tone = value <= 25 ? "danger" : value <= 50 ? "warn" : "";
      return `
        <div class="stat-row">
          <span class="stat-label">${label}</span>
          <div class="stat-track" aria-label="${label}: ${value}">
            <div class="stat-fill ${tone}" style="width: ${value}%"></div>
          </div>
          <span class="stat-value">${value}</span>
        </div>
      `;
    })
    .join("");
}

function renderActions() {
  if (state.actions.length === 0) {
    els.actionsList.innerHTML = '<p class="muted">Actions indisponibles.</p>';
    return;
  }

  els.actionsList.innerHTML = state.actions
    .map((action) => {
      const effects = Object.entries(action.effects)
        .filter(([, value]) => value !== 0)
        .map(([key, value]) => `${labelForEffect(key)} ${value > 0 ? "+" : ""}${value}`)
        .join(" - ");

      return `
        <article class="action-item">
          <strong>${escapeHtml(action.name)}</strong>
          <span class="action-effect">${escapeHtml(effects || "Aucun effet")}</span>
          <span class="action-effect">Duree ${action.duration}</span>
        </article>
      `;
    })
    .join("");
}

function renderCharacter(character) {
  state.selected = character;

  if (!character) {
    els.emptyState.classList.remove("hidden");
    els.dashboard.classList.add("hidden");
    return;
  }

  els.emptyState.classList.add("hidden");
  els.dashboard.classList.remove("hidden");

  els.characterName.textContent = character.name;
  els.characterPrompt.textContent = character.prompt;
  els.feelingText.textContent = character.feeling || "Je vais bien.";
  els.lastActionText.textContent = `Derniere action: ${character.lastAction || "spawn"}`;
  els.moneyValue.textContent = character.money;
  els.foodValue.textContent = character.food;
  els.ticksValue.textContent = character.currentAction
    ? `${character.currentAction} (${character.actionTicksLeft})`
    : "Libre";
  els.updatedAt.textContent = character.lastUpdate ? `Maj ${formatDate(character.lastUpdate)}` : "";

  els.lifeBadge.textContent = character.isAlive ? "Vivant" : "Mort";
  els.lifeBadge.classList.toggle("dead", !character.isAlive);

  els.petVisual.classList.toggle("dead", !character.isAlive);
  els.petVisual.classList.toggle(
    "weak",
    character.isAlive &&
      Math.min(character.hp, character.hunger, character.energy, character.hygiene, character.mental) <= 25
  );

  els.tickButton.disabled = !character.isAlive || state.loading;
  els.multiTickButton.disabled = !character.isAlive || state.loading;

  renderStats(character);
  renderCharacters();
}

function renderLogs(logs) {
  if (!logs || logs.length === 0) {
    els.logList.innerHTML = '<li><p>Aucun log.</p></li>';
    return;
  }

  els.logList.innerHTML = logs
    .map(
      (log) => `
        <li>
          <strong>${escapeHtml(log.action)}</strong>
          <p>${escapeHtml(log.message)}</p>
          <time>${formatDate(log.createdAt)}</time>
        </li>
      `
    )
    .join("");
}

function labelForEffect(key) {
  const labels = {
    hp: "vie",
    hunger: "faim",
    energy: "energie",
    hygiene: "hygiene",
    mental: "mental",
    entertainment: "loisir",
    money: "argent",
    food: "nourriture",
  };
  return labels[key] || key;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadCharacters() {
  state.characters = await request("/characters");

  if (!state.selectedId && state.characters.length > 0) {
    state.selectedId = state.characters[0].id;
  }

  renderCharacters();

  if (state.selectedId) {
    await selectCharacter(state.selectedId);
  } else {
    renderCharacter(null);
  }
}

async function loadActions() {
  state.actions = await request("/actions");
  renderActions();
}

async function loadLogs() {
  if (!state.selectedId) {
    renderLogs([]);
    return;
  }
  const logs = await request(`/characters/${state.selectedId}/logs?limit=30`);
  renderLogs(logs);
}

async function selectCharacter(id) {
  state.selectedId = Number(id);
  const character = await request(`/characters/${state.selectedId}`);
  renderCharacter(character);
  await loadLogs();
}

async function createCharacter(event) {
  event.preventDefault();
  const payload = {
    name: els.nameInput.value.trim(),
    prompt: els.promptInput.value.trim(),
  };

  if (!payload.name || !payload.prompt) {
    showToast("Nom et prompt requis.");
    return;
  }

  setLoading(true);
  try {
    const character = await request("/characters", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    els.createForm.reset();
    state.selectedId = character.id;
    showToast(`${character.name} est cree.`);
    await loadCharacters();
  } catch (error) {
    showToast(error.message);
  } finally {
    setLoading(false);
  }
}

async function tick(count = 1) {
  if (!state.selectedId) {
    return;
  }

  setLoading(true);
  try {
    const path = count === 1 ? `/characters/${state.selectedId}/tick` : `/characters/${state.selectedId}/ticks`;
    const result = await request(path, {
      method: "POST",
      body: count === 1 ? undefined : JSON.stringify({ count }),
    });
    renderCharacter(result.character);
    await loadCharacters();
    await loadLogs();
  } catch (error) {
    showToast(error.message);
  } finally {
    setLoading(false);
  }
}

async function deleteSelected() {
  if (!state.selectedId || !window.confirm("Supprimer ce personnage ?")) {
    return;
  }

  setLoading(true);
  try {
    await request(`/characters/${state.selectedId}`, { method: "DELETE" });
    state.selectedId = null;
    state.selected = null;
    showToast("Personnage supprime.");
    await loadCharacters();
  } catch (error) {
    showToast(error.message);
  } finally {
    setLoading(false);
  }
}

async function init() {
  setLoading(true);
  try {
    await request("/health");
    updateApiStatus(true);
    await Promise.all([loadActions(), loadCharacters()]);
  } catch (error) {
    updateApiStatus(false);
    showToast("Backend indisponible sur http://127.0.0.1:5000");
    renderCharacter(null);
  } finally {
    setLoading(false);
  }
}

els.createForm.addEventListener("submit", createCharacter);
els.refreshButton.addEventListener("click", async () => {
  setLoading(true);
  try {
    await loadCharacters();
  } catch (error) {
    showToast(error.message);
  } finally {
    setLoading(false);
  }
});

els.characterList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-id]");
  if (!button) {
    return;
  }

  setLoading(true);
  try {
    await selectCharacter(button.dataset.id);
  } catch (error) {
    showToast(error.message);
  } finally {
    setLoading(false);
  }
});

els.tickButton.addEventListener("click", () => tick(1));
els.multiTickButton.addEventListener("click", () => tick(10));
els.deleteButton.addEventListener("click", deleteSelected);
els.logsButton.addEventListener("click", async () => {
  try {
    await loadLogs();
  } catch (error) {
    showToast(error.message);
  }
});

init();
