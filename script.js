// Mobile nav toggle
const toggle = document.querySelector(".nav-toggle");
const links = document.querySelector(".nav-links");

if (toggle && links) {
  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });

  // Close menu when a link is clicked (mobile)
  links.querySelectorAll("a").forEach((a) => {
    a.addEventListener("click", () => {
      links.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

// Current year in footer
const yearEl = document.getElementById("year");
if (yearEl) yearEl.textContent = new Date().getFullYear();

// ---------------- Language toggle (EN / DE) ----------------
function applyLanguage(lang) {
  const attr = lang === "de" ? "data-de" : "data-en";
  document.querySelectorAll("[data-en]").forEach((el) => {
    const val = el.getAttribute(attr);
    if (val !== null) el.innerHTML = val;
  });

  // Update <html lang>
  document.documentElement.setAttribute("lang", lang);

  // Update the toggle's active state
  document.querySelectorAll(".lang-opt").forEach((opt) => {
    opt.classList.toggle("active", opt.getAttribute("data-lang") === lang);
  });

  // Persist choice
  try {
    localStorage.setItem("cv-lang", lang);
  } catch (e) {
    /* ignore */
  }
}

const langToggle = document.getElementById("lang-toggle");
if (langToggle) {
  langToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("lang") === "de" ? "de" : "en";
    applyLanguage(current === "de" ? "en" : "de");
  });
}

// Initialise from saved preference (default: English)
(function initLang() {
  let saved = "en";
  try {
    saved = localStorage.getItem("cv-lang") || "en";
  } catch (e) {
    /* ignore */
  }
  applyLanguage(saved);
})();
