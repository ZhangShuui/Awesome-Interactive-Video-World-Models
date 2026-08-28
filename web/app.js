/* Filtering for the index.
 *
 * Every row is already in the HTML -- the page is readable and searchable with
 * JavaScript off, which for a bibliography is the point. This file only hides
 * rows, so the no-JS state is the complete list rather than an empty shell.
 *
 * Filter state lives in the URL hash, so a filtered view is a link you can
 * send someone: #tag=systems,memory&q=diffusion&demo=1
 */
(function () {
  "use strict";

  var rows = Array.prototype.slice.call(document.querySelectorAll(".row"));
  if (!rows.length) return;

  var input = document.getElementById("q");
  var list = document.getElementById("rows");
  var empty = document.getElementById("empty");
  var shown = document.getElementById("shown");
  var sortBtn = document.getElementById("sort");
  var resetBtn = document.getElementById("reset");

  var tagButtons = Array.prototype.slice.call(document.querySelectorAll("[data-tag]"));
  var flagButtons = Array.prototype.slice.call(document.querySelectorAll("[data-flag]"));

  var state = { q: "", tags: [], flags: [], oldest: false };

  /* ---------------------------------------------------------------- hash -- */

  function readHash() {
    var raw = (location.hash || "").replace(/^#/, "");
    if (!raw) return;
    raw.split("&").forEach(function (pair) {
      var i = pair.indexOf("=");
      if (i < 0) return;
      var k = decodeURIComponent(pair.slice(0, i));
      var v = decodeURIComponent(pair.slice(i + 1));
      if (k === "q") state.q = v;
      else if (k === "tag") state.tags = v.split(",").filter(Boolean);
      else if (k === "flag") state.flags = v.split(",").filter(Boolean);
      else if (k === "sort") state.oldest = v === "oldest";
    });
  }

  function writeHash() {
    var parts = [];
    if (state.q) parts.push("q=" + encodeURIComponent(state.q));
    if (state.tags.length) parts.push("tag=" + state.tags.join(","));
    if (state.flags.length) parts.push("flag=" + state.flags.join(","));
    if (state.oldest) parts.push("sort=oldest");
    var next = parts.length ? "#" + parts.join("&") : " ";
    // replaceState keeps the back button meaning "the page before this one"
    // rather than "the last keystroke".
    history.replaceState(null, "", location.pathname + location.search + (parts.length ? next : ""));
  }

  /* --------------------------------------------------------------- apply -- */

  function matches(row) {
    if (state.q) {
      var hay = row.getAttribute("data-search") || "";
      var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
      for (var i = 0; i < terms.length; i++) {
        if (hay.indexOf(terms[i]) === -1) return false;
      }
    }
    if (state.tags.length) {
      // AND across tags: papers carry several, and "systems + memory" is a
      // narrowing question, not a widening one.
      var mine = (row.getAttribute("data-tags") || "").split(" ");
      for (var j = 0; j < state.tags.length; j++) {
        if (mine.indexOf(state.tags[j]) === -1) return false;
      }
    }
    for (var k = 0; k < state.flags.length; k++) {
      if (row.getAttribute("data-" + state.flags[k]) !== "1") return false;
    }
    return true;
  }

  function apply() {
    var n = 0;
    for (var i = 0; i < rows.length; i++) {
      var ok = matches(rows[i]);
      rows[i].classList.toggle("is-hidden", !ok);
      if (ok) n++;
    }
    shown.textContent = String(n);
    empty.hidden = n !== 0;
    list.classList.toggle("is-oldest", state.oldest);

    tagButtons.forEach(function (b) {
      b.setAttribute("aria-pressed", state.tags.indexOf(b.getAttribute("data-tag")) > -1 ? "true" : "false");
    });
    flagButtons.forEach(function (b) {
      b.setAttribute("aria-pressed", state.flags.indexOf(b.getAttribute("data-flag")) > -1 ? "true" : "false");
    });
    if (sortBtn) sortBtn.textContent = state.oldest ? "OLDEST FIRST" : "NEWEST FIRST";
    if (input && input.value !== state.q) input.value = state.q;

    writeHash();
  }

  function toggle(arr, value) {
    var i = arr.indexOf(value);
    if (i > -1) arr.splice(i, 1);
    else arr.push(value);
  }

  /* --------------------------------------------------------------- wire -- */

  tagButtons.forEach(function (b) {
    b.addEventListener("click", function () {
      toggle(state.tags, b.getAttribute("data-tag"));
      apply();
    });
  });

  flagButtons.forEach(function (b) {
    b.addEventListener("click", function () {
      toggle(state.flags, b.getAttribute("data-flag"));
      apply();
    });
  });

  if (input) {
    var timer = null;
    input.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        state.q = input.value.trim();
        apply();
      }, 90);
    });
  }

  if (sortBtn) {
    sortBtn.addEventListener("click", function () {
      state.oldest = !state.oldest;
      apply();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      state = { q: "", tags: [], flags: [], oldest: state.oldest };
      apply();
    });
  }

  // "/" focuses search the way it does in every reader; Escape lets go.
  document.addEventListener("keydown", function (e) {
    if (e.key === "/" && document.activeElement !== input) {
      e.preventDefault();
      input.focus();
      input.select();
    } else if (e.key === "Escape" && document.activeElement === input) {
      input.blur();
    }
  });

  readHash();
  apply();
})();
