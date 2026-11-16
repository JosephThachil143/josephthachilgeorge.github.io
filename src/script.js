/* Site script. Loaded from <head>; no inline JS anywhere (strict CSP). */
(function () {
  "use strict";

  // Progressive enhancement flag: styles for the collapsible nav only apply with JS.
  document.documentElement.classList.add("js");

  // Legacy links (?lang=de) -> static German page.
  try {
    var params = new URLSearchParams(location.search);
    var wanted = params.get("lang");
    if (wanted === "de" && location.pathname.indexOf("/de/") !== 0) {
      var path = location.pathname === "/" ? "/index.html" : location.pathname;
      location.replace("/de" + (path === "/index.html" ? "/" : path) + location.hash);
      return;
    }
    if (wanted === "en" && location.search) {
      history.replaceState(null, "", location.pathname + location.hash);
    }
  } catch (e) { /* ignore */ }

  document.addEventListener("DOMContentLoaded", function () {
    // Mobile nav toggle
    var toggle = document.querySelector(".nav-toggle");
    var links = document.querySelector(".nav-links");
    if (toggle && links) {
      toggle.addEventListener("click", function () {
        var open = links.classList.toggle("open");
        toggle.setAttribute("aria-expanded", String(open));
      });
      links.querySelectorAll("a").forEach(function (a) {
        a.addEventListener("click", function () {
          links.classList.remove("open");
          toggle.setAttribute("aria-expanded", "false");
        });
      });
    }

    // CV download modal (home page)
    var dlBtn = document.getElementById("download-cv");
    var cvModal = document.getElementById("cv-modal");
    var cvClose = document.getElementById("cv-modal-close");
    var lastFocus = null;
    function openCvModal() {
      if (!cvModal) return;
      lastFocus = document.activeElement;
      cvModal.classList.add("open");
      cvModal.setAttribute("aria-hidden", "false");
      var first = cvModal.querySelector("a, button");
      if (first) first.focus();
    }
    function closeCvModal() {
      if (!cvModal) return;
      cvModal.classList.remove("open");
      cvModal.setAttribute("aria-hidden", "true");
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    if (dlBtn) dlBtn.addEventListener("click", openCvModal);
    if (cvClose) cvClose.addEventListener("click", closeCvModal);
    if (cvModal) {
      cvModal.addEventListener("click", function (e) {
        if (e.target === cvModal) closeCvModal();
      });
    }
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeCvModal();
    });

    // CV page: print / save as PDF
    var printBtn = document.querySelector(".tb-print");
    if (printBtn) printBtn.addEventListener("click", function () { window.print(); });
  });
})();
