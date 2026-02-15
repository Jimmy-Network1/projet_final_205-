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
