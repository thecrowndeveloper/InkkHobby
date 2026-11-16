/* InkHobby: small, dependency-free enhancements. The site works without any of this. */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  // Site theme: dark (default) or light. The startup script in <head> applies the saved choice before first paint.
  var root = document.documentElement;
  var syncThemeUI = function () {
    var light = root.dataset.theme === "light";
    $$("[data-theme-label]").forEach(function (el) { el.textContent = light ? "dark" : "light"; });
    $$("[data-theme-toggle]").forEach(function (b) { b.setAttribute("aria-pressed", String(light)); });
  };
  $$("[data-theme-toggle]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
      store.set("ink-theme", root.dataset.theme);
      syncThemeUI();
      document.dispatchEvent(new CustomEvent("ink:theme"));
    });
  });
  syncThemeUI();

  // Mobile nav
  var navBtn = $("[data-nav-toggle]"), nav = $("#primary-nav");
  if (navBtn && nav) navBtn.addEventListener("click", function () {
    var open = nav.classList.toggle("is-open");
    navBtn.setAttribute("aria-expanded", String(open));
  });

  // Close open dropdowns when clicking elsewhere
  document.addEventListener("click", function (e) {
    $$("details.menu[open], details.account[open]").forEach(function (d) { if (!d.contains(e.target)) d.removeAttribute("open"); });
  });

  // Toasts fade out
  $$(".toast").forEach(function (t, i) {
    setTimeout(function () { t.classList.add("is-leaving"); setTimeout(function () { t.remove(); }, 350); }, 5000 + i * 800);
  });

  // First-visit guide
  var guide = $("[data-concierge]");
  if (guide && !store.get("ink-welcomed")) {
    guide.hidden = false;
    $$("[data-concierge-close]").forEach(function (b) {
      b.addEventListener("click", function () { guide.hidden = true; store.set("ink-welcomed", "1"); });
    });
  }

  // Share: copy link, or use the native share sheet where available
  $$("[data-share]").forEach(function (box) {
    var btn = $("[data-copy-link]", box);
    if (!btn) return;
    btn.addEventListener("click", function () {
      var url = box.dataset.url, title = box.dataset.title;
      if (navigator.share && /Mobi|Android/i.test(navigator.userAgent)) {
        navigator.share({ title: title, url: url }).catch(function () {});
        return;
      }
      var done = function () { btn.textContent = "Copied ✓"; setTimeout(function () { btn.textContent = "Copy link"; }, 2000); };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () { window.prompt("Copy this link", url); });
      else window.prompt("Copy this link", url);
    });
  });

  // Home spotlight: thumbnails switch the featured story, auto-advancing until the visitor interacts
  var spot = $("[data-spotlight]");
  if (spot) {
    var slides = $$("[data-slide]", spot), thumbs = $$("[data-thumb]", spot), bg = $("[data-spot-bg]", spot);
    var current = 0, timer = null;
    var show = function (i) {
      current = (i + slides.length) % slides.length;
      slides.forEach(function (s, n) { s.classList.toggle("is-active", n === current); });
      thumbs.forEach(function (t, n) { t.classList.toggle("is-active", n === current); t.setAttribute("aria-selected", String(n === current)); });
      if (bg) bg.style.setProperty("--h", slides[current].dataset.hue);
    };
    var stop = function () { if (timer) { clearInterval(timer); timer = null; } };
    thumbs.forEach(function (t, n) { t.addEventListener("click", function () { stop(); show(n); }); });
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (slides.length > 1 && !reduce) {
      timer = setInterval(function () { show(current + 1); }, 7000);
      spot.addEventListener("pointerenter", stop);
      spot.addEventListener("focusin", stop);
    }
  }

  // Reading room
  var reader = $("[data-reader]");
  if (!reader) return;

  // Keyboard: ← previous chapter, → next chapter (ignored while typing)
  document.addEventListener("keydown", function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return;
    var link = e.key === "ArrowRight" ? $("[data-next]") : e.key === "ArrowLeft" ? $("[data-prev]") : null;
    if (link) window.location.href = link.href;
  });

  var size = parseFloat(store.get("ink-size")) || 1.2;
  var widths = [34, 38, 46], wi = parseInt(store.get("ink-width") || "1", 10);
  var applySize = function () { reader.style.setProperty("--rs", size + "rem"); };
  var applyWidth = function () { reader.style.setProperty("--rw", widths[wi] + "rem"); };
  // Reader theme: "auto" follows the site theme; dark / light / sepia are explicit overrides.
  var themeSel = $("[data-reader-theme-select]", reader);
  var VALID = { night: 1, paper: 1, sepia: 1 };
  var savedTheme = store.get("ink-reader-theme");
  if (!VALID[savedTheme]) savedTheme = "auto";
  var applyReaderTheme = function (v) {
    if (VALID[v]) reader.dataset.readerTheme = v; else reader.removeAttribute("data-reader-theme");
  };
  applyReaderTheme(savedTheme);
  if (themeSel) {
    themeSel.value = savedTheme;
    themeSel.addEventListener("change", function () { applyReaderTheme(themeSel.value); store.set("ink-reader-theme", themeSel.value); });
  }
  applySize(); applyWidth();

  $$("[data-size]", reader).forEach(function (b) {
    b.addEventListener("click", function () {
      size = Math.min(1.7, Math.max(.95, size + parseInt(b.dataset.size, 10) * 0.08));
      applySize(); store.set("ink-size", size);
    });
  });
  var widthBtn = $("[data-width]", reader);
  if (widthBtn) widthBtn.addEventListener("click", function () { wi = (wi + 1) % widths.length; applyWidth(); store.set("ink-width", wi); });

  // Reading progress hairline
  var bar = $("[data-progress]");
  var text = $("[data-text]", reader);
  if (bar && text) {
    var tick = function () {
      var r = text.getBoundingClientRect(), total = r.height - window.innerHeight * 0.6;
      var pct = total > 0 ? Math.min(1, Math.max(0, (-r.top + window.innerHeight * 0.2) / total)) : 0;
      bar.style.width = (pct * 100) + "%";
    };
    window.addEventListener("scroll", tick, { passive: true }); tick();
  }

  // Translation
  var sel = $("[data-translate]", reader), status = $("[data-translate-status]", reader), orig = $("[data-show-original]", reader);
  if (sel && text) {
    var original = text.innerHTML;
    var say = function (msg) { status.hidden = !msg; status.textContent = msg || ""; };
    sel.addEventListener("change", function () {
      var lang = sel.value;
      if (!lang) { text.innerHTML = original; orig.hidden = true; say(""); return; }
      say("Translating…");
      fetch(reader.dataset.chapterUrl + "?lang=" + encodeURIComponent(lang), { credentials: "same-origin", headers: { Accept: "application/json" } })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (res) {
          if (!res.ok) { say(res.d.error || "Translation isn't available right now."); sel.value = ""; return; }
          text.innerHTML = "";
          res.d.paragraphs.forEach(function (p) { var el = document.createElement("p"); el.textContent = p; text.appendChild(el); });
          text.setAttribute("lang", lang);
          orig.hidden = false;
          say("Machine translation, so some nuance may be lost.");
        })
        .catch(function () { say("We couldn't reach the translator. Please try again."); sel.value = ""; });
    });
    orig.addEventListener("click", function () { text.innerHTML = original; text.removeAttribute("lang"); sel.value = ""; orig.hidden = true; say(""); });
  }
})();
