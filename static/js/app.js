function copyToClipboard(text) {
  if (!text) return false;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text);
    return true;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "absolute";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
  return true;
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-copy-target]");
  if (!button) return;
  const selector = button.getAttribute("data-copy-target");
  const input = document.querySelector(selector);
  if (!input) return;
  if (copyToClipboard(input.value || input.textContent)) {
    const original = button.textContent;
    button.textContent = "Copié";
    window.setTimeout(() => (button.textContent = original), 1200);
  }
});

function setTheme(theme) {
  const normalized = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = normalized;
  try {
    localStorage.setItem("theme", normalized);
  } catch (_) {}
}

function initTheme() {
  let theme = "light";
  try {
    theme = localStorage.getItem("theme") || theme;
  } catch (_) {}
  if (!theme) theme = "light";
  setTheme(theme);
}

document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-theme-toggle]");
  if (!toggle) return;
  const current = document.documentElement.dataset.theme || "light";
  setTheme(current === "dark" ? "light" : "dark");
});

initTheme();

// ======================
// Filtres (listings)
// ======================

// Retire un ou plusieurs paramètres de la query-string puis recharge
document.addEventListener("click", (event) => {
  const chip = event.target.closest("[data-remove-filter]");
  if (!chip) return;
  const paramsToRemove = (chip.getAttribute("data-remove-filter") || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  if (!paramsToRemove.length) return;

  const url = new URL(window.location.href);
  paramsToRemove.forEach((p) => url.searchParams.delete(p));
  // Si la page était paginée, on revient à la page 1
  url.searchParams.delete("page");
  window.location.href = url.toString();
});

// Boutons de presets pour remplir rapidement le formulaire de filtres (mobile/offcanvas)
document.addEventListener("click", (event) => {
  const btn = event.target.closest("[data-quick-filter]");
  if (!btn) return;

  const formSelector = btn.getAttribute("data-form") || "#filtersFormMobile";
  const form = document.querySelector(formSelector);
  if (!form) return;

  const presets = (btn.getAttribute("data-quick-filter") || "").split(",");
  presets.forEach((pair) => {
    const [name, value] = pair.split("=");
    if (!name) return;
    const input = form.querySelector(`[name="${name}"]`);
    if (input) input.value = value ?? "";
  });

  // Remettre la pagination à 1
  const pageInput = form.querySelector('[name="page"]');
  if (pageInput) pageInput.value = "";

  form.submit();
});
