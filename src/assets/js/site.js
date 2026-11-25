/* Amy African Hair Braiding & Boutique — interactions (no dependencies) */
(function () {
  "use strict";
  document.documentElement.classList.add("js");
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduced = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  var saveData = !!(navigator.connection && navigator.connection.saveData);

  /* ---------- header: hairline + shadow once scrolled */
  var head = $("[data-head]");
  var onScroll = function () { if (head) head.classList.toggle("is-scrolled", window.scrollY > 8); };
  window.addEventListener("scroll", onScroll, { passive: true }); onScroll();

  /* ---------- mobile menu (white sheet): scroll lock, focus trap, Escape, tap outside */
  var menu = $("[data-menu]"), openBtn = $("[data-menu-open]"), closeBtn = $("[data-menu-close]");
  if (menu && openBtn) {
    var setMenu = function (open, keepFocus) {
      menu.hidden = !open;
      openBtn.setAttribute("aria-expanded", String(open));
      document.body.classList.toggle("menu-open", open);
      if (open) closeBtn.focus(); else if (!keepFocus) openBtn.focus();
    };
    openBtn.addEventListener("click", function () { setMenu(true); });
    closeBtn.addEventListener("click", function () { setMenu(false); });
    menu.addEventListener("click", function (ev) { if (ev.target === menu) setMenu(false); });
    $$("a", menu).forEach(function (a) { a.addEventListener("click", function () { setMenu(false, true); }); });
    document.addEventListener("keydown", function (ev) {
      if (menu.hidden) return;
      if (ev.key === "Escape") return setMenu(false);
      if (ev.key === "Tab") {
        var f = $$("a, button", menu), first = f[0], last = f[f.length - 1];
        if (ev.shiftKey && document.activeElement === first) { ev.preventDefault(); last.focus(); }
        else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
      }
    });
    window.addEventListener("resize", function () { if (window.innerWidth > 960 && !menu.hidden) setMenu(false, true); });
    window.addEventListener("pageshow", function () { menu.hidden = true; document.body.classList.remove("menu-open"); });
  }

  /* ---------- hero video: Amy at work. Muted loop, never blocks the page.
     Starts after the page has loaded; poster stays for reduced motion / Data Saver / failures. Pause button always available. */
  var hero = $("[data-hero]");
  if (hero) {
    var hv = $("[data-hero-video]", hero), hb = $("[data-hero-toggle]", hero), hl = $("[data-hero-label]", hero);
    var loaded = false, userPaused = false, failed = false;
    var setState = function (s) { hero.setAttribute("data-state", s); if (hl) hl.textContent = s === "playing" ? "Pause video" : "Play video"; };
    var fail = function () { failed = true; setState("poster"); if (hb) hb.hidden = true; };
    var load = function () {
      if (loaded) return; loaded = true;
      $$("source", hv).forEach(function (s) { s.src = s.getAttribute("data-src"); });
      var srcs = $$("source", hv); if (srcs.length) srcs[srcs.length - 1].addEventListener("error", fail);
      hv.addEventListener("error", fail);
      hv.load();
    };
    var play = function () {
      if (failed) return; load();
      var p = hv.play(); if (p && p.catch) p.catch(function () { setState("poster"); });
    };
    hv.addEventListener("playing", function () { setState("playing"); });
    hv.addEventListener("pause", function () { if (!failed) setState(loaded ? "paused" : "poster"); });
    setState("poster");
    if (hb) {
      hb.hidden = false;
      hb.addEventListener("click", function () { if (hv.paused) { userPaused = false; play(); } else { userPaused = true; hv.pause(); } });
    }
    var auto = function () { return !(reduced && reduced.matches) && !saveData; };
    var start = function () { if (auto()) play(); };
    if (document.readyState === "complete") start(); else window.addEventListener("load", start);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) {
        if (!loaded) return;
        if (es[0].isIntersecting) { if (!userPaused && auto() && hv.paused) play(); }
        else if (!hv.paused) hv.pause();
      }, { threshold: 0.2 }).observe(hero);
    }
    if (reduced && reduced.addEventListener) reduced.addEventListener("change", function () { if (reduced.matches && !hv.paused) hv.pause(); });
  }

  /* ---------- discreet booking pill on phones: after the hero, hidden over the form and footer */
  var bar = $("[data-mbar]");
  if (bar) {
    var hideOver = $$("#book, [data-foot], .final");
    var upd = function () {
      var vh = window.innerHeight, show = window.scrollY > vh * 0.7;
      hideOver.forEach(function (el) { var r = el.getBoundingClientRect(); if (r.top < vh - 40 && r.bottom > 0) show = false; });
      if (document.body.classList.contains("menu-open") || document.body.classList.contains("lb-open")) show = false;
      bar.classList.toggle("is-on", show);
      bar.setAttribute("aria-hidden", String(!show));
      bar.tabIndex = show ? 0 : -1;
    };
    var tick = false;
    window.addEventListener("scroll", function () { if (!tick) { tick = true; requestAnimationFrame(function () { tick = false; upd(); }); } }, { passive: true });
    window.addEventListener("resize", upd); upd();
  }

  /* ---------- style filters */
  $$("[data-filter-group]").forEach(function (group) {
    var target = $('[data-filter-target="' + group.getAttribute("data-filter-group") + '"]');
    if (!target) return;
    group.addEventListener("click", function (ev) {
      var btn = ev.target.closest("[data-filter]"); if (!btn) return;
      var v = btn.getAttribute("data-filter");
      $$("[data-filter]", group).forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      $$("[data-cat]", target).forEach(function (card) { card.hidden = !(v === "all" || card.getAttribute("data-cat") === v); });
    });
  });

  /* ---------- lightbox: swipe, arrows, keyboard; follows the active filter; Book this look */
  var lb = $("[data-lb]");
  if (lb) {
    var lbImg = $("[data-lb-img]", lb), lbCap = $("[data-lb-cap]", lb), lbBook = $("[data-lb-book]", lb), lbCount = $("[data-lb-count]", lb);
    var list = [], idx = 0, lastFocus = null, sx = null, sy = null;
    var show = function (i) {
      idx = (i + list.length) % list.length;
      var b = list[idx];
      lbImg.src = b.getAttribute("data-lightbox"); lbImg.alt = b.getAttribute("data-alt") || "";
      lbCap.textContent = b.getAttribute("data-cap") || "";
      var link = b.getAttribute("data-book"); lbBook.hidden = !link; if (link) lbBook.href = link;
      lbCount.textContent = (idx + 1) + " / " + list.length;
    };
    var closeLb = function () { lb.hidden = true; lbImg.removeAttribute("src"); document.body.classList.remove("lb-open"); if (lastFocus) lastFocus.focus(); };
    $$("[data-lightbox]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        list = $$("[data-lightbox]").filter(function (x) { var li = x.closest("[data-cat]"); return !(li && li.hidden); });
        lastFocus = btn; lb.hidden = false; document.body.classList.add("lb-open");
        show(list.indexOf(btn)); $("[data-lb-close]", lb).focus();
      });
    });
    $("[data-lb-prev]", lb).addEventListener("click", function () { show(idx - 1); });
    $("[data-lb-next]", lb).addEventListener("click", function () { show(idx + 1); });
    lb.addEventListener("click", function (ev) { if (ev.target === lb || ev.target.closest("[data-lb-close]")) closeLb(); });
    lb.addEventListener("touchstart", function (ev) { sx = ev.touches[0].clientX; sy = ev.touches[0].clientY; }, { passive: true });
    lb.addEventListener("touchend", function (ev) {
      if (sx === null) return;
      var dx = ev.changedTouches[0].clientX - sx, dy = ev.changedTouches[0].clientY - sy; sx = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(idx + (dx < 0 ? 1 : -1));
      else if (dy > 90) closeLb();
    });
    document.addEventListener("keydown", function (ev) {
      if (lb.hidden) return;
      if (ev.key === "Escape") closeLb();
      else if (ev.key === "ArrowRight") show(idx + 1);
      else if (ev.key === "ArrowLeft") show(idx - 1);
      else if (ev.key === "Tab") {
        var f = $$("button, a:not([hidden])", lb), first = f[0], last = f[f.length - 1];
        if (ev.shiftKey && document.activeElement === first) { ev.preventDefault(); last.focus(); }
        else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
      }
    });
  }

  /* ---------- only one video plays at a time */
  document.addEventListener("play", function (ev) {
    if (ev.target.tagName !== "VIDEO") return;
    $$("video").forEach(function (v) { if (v !== ev.target && !v.paused && !v.muted) v.pause(); });
    if (!ev.target.muted) $$("video[muted], video").forEach(function (v) { if (v !== ev.target && !v.paused) v.pause(); });
  }, true);

  /* ---------- salon film: tap to play with sound; nothing downloads before that */
  $$("[data-showcase]").forEach(function (sc) {
    var sv = $("[data-showcase-video]", sc), sp = $("[data-showcase-play]", sc);
    if (!sv || !sp) return;
    sp.hidden = false;
    sp.addEventListener("click", function () { sc.classList.add("was-played"); var r = sv.play(); if (r && r.catch) r.catch(function () {}); });
    sv.addEventListener("play", function () { sc.classList.add("is-playing", "was-played"); });
    sv.addEventListener("pause", function () { sc.classList.remove("is-playing"); });
  });

  /* ---------- Instagram / TikTok cards (only rendered when a real cover exists): load on tap */
  var igState = "idle", igWait = [];
  var loadIg = function (cb) {
    if (igState === "ready") return cb(true);
    if (igState === "failed") return cb(false);
    igWait.push(cb); if (igState === "loading") return;
    igState = "loading";
    var s = document.createElement("script"); s.async = true; s.src = "https://www.instagram.com/embed.js";
    s.onload = function () { igState = "ready"; igWait.splice(0).forEach(function (f) { f(true); }); };
    s.onerror = function () { igState = "failed"; igWait.splice(0).forEach(function (f) { f(false); }); };
    document.body.appendChild(s);
  };
  $$("[data-load]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var card = btn.closest(".vt"), box = $("[data-embed]", card), kind = card.getAttribute("data-kind");
      var out = card.getAttribute("data-permalink") || card.getAttribute("data-url");
      if (kind === "tiktok" && card.getAttribute("data-vid")) {
        var f = document.createElement("iframe");
        f.src = "https://www.tiktok.com/player/v1/" + card.getAttribute("data-vid") + "?music_info=0&description=0&rel=0&autoplay=1";
        f.title = "TikTok video"; f.setAttribute("allow", "autoplay; fullscreen; encrypted-media"); f.setAttribute("allowfullscreen", "");
        f.style.cssText = "position:absolute;inset:0;width:100%;height:100%;border:0";
        box.appendChild(f); btn.hidden = true; return;
      }
      if (kind === "instagram") {
        var bq = document.createElement("blockquote");
        bq.className = "instagram-media"; bq.setAttribute("data-instgrm-permalink", out); bq.setAttribute("data-instgrm-version", "14");
        box.appendChild(bq);
        loadIg(function (ok) { if (ok && window.instgrm) { window.instgrm.Embeds.process(); btn.hidden = true; } else { box.innerHTML = ""; window.location.href = out; } });
        return;
      }
      window.location.href = out;
    });
  });

  /* ---------- booking form */
  var form = $("[data-book]");
  if (form) {
    var params = new URLSearchParams(location.search);
    var style = params.get("style"), sel = $("#b-style", form);
    if (style && sel && $$("option", sel).some(function (o) { return o.value === style; })) sel.value = style;
    /* "Book this look": show the chosen photo and carry it into the request */
    var look = params.get("look"), img = params.get("img"), lookBox = $("[data-look]", form), lookIn = $("[data-look-input]", form);
    if (look && lookBox) {
      $("[data-look-text]", lookBox).textContent = (style ? style + " · " : "") + look.slice(0, 160);
      var li = $("[data-look-img]", lookBox);
      if (img && /^images\/[\w\/.-]+$/.test(img)) { li.src = img; li.alt = look.slice(0, 120); } else { li.remove(); lookBox.style.gridTemplateColumns = "minmax(0,1fr) auto"; }
      lookBox.hidden = false;
      lookIn.value = (style ? style + ": " : "") + look.slice(0, 200);
      $("[data-look-clear]", lookBox).addEventListener("click", function () { lookBox.hidden = true; lookIn.value = ""; });
    }
    var d = $("#b-date", form);
    if (d) { var t = new Date(); t.setMinutes(t.getMinutes() - t.getTimezoneOffset()); d.min = t.toISOString().slice(0, 10); }
    var msg = $("[data-msg]", form), btn = $("[data-submit]", form);
    var setMsg = function (text, kind) { msg.textContent = text; msg.className = "form-msg" + (kind ? " " + kind : ""); };
    var MAX = 8 * 1024 * 1024;
    var MSG = { name: "Please enter your name.", phone: "Please enter a phone number Amy can call or text.", style: "Please choose a hairstyle.",
      email: "Please check your email address, or leave it empty.", date: "Please choose a date from today onwards.", time: "Please choose a time of day." };
    var setErr = function (f, text) {
      f.setAttribute("aria-invalid", text ? "true" : "false");
      var p = document.getElementById(f.id + "-err"); if (p) p.textContent = text || "";
    };
    $$("input, select, textarea", form).forEach(function (f) {
      var clear = function () { if (f.getAttribute("aria-invalid") === "true" && f.checkValidity()) setErr(f, ""); };
      f.addEventListener("input", clear); f.addEventListener("change", clear);
    });
    form.addEventListener("submit", function (ev) {
      ev.preventDefault(); setMsg("");
      var bad = null;
      $$("input, select, textarea", form).forEach(function (f) {
        if (f.type === "hidden" || f.name === "company" || f.type === "file" || !f.id) return;
        var ok = f.checkValidity();
        setErr(f, ok ? "" : (MSG[f.name] || "Please check this field."));
        if (!ok && !bad) bad = f;
      });
      var file = $("#b-photo", form);
      if (file && file.files[0]) {
        var fl = file.files[0], okType = /^image\//.test(fl.type || "image/") || /\.(heic|heif)$/i.test(fl.name);
        if (fl.size > MAX || !okType) { setErr(file, fl.size > MAX ? "This photo is larger than 8 MB. Please choose a smaller one." : "Please choose an image file."); if (!bad) { bad = file; $(".more-f", form).open = true; } }
        else setErr(file, "");
      }
      if (bad) { setMsg("Please check the highlighted fields.", "err"); bad.focus(); return; }
      btn.disabled = true;
      var label = btn.querySelector("span"), old = label.textContent; label.textContent = "Sending…";
      fetch("/", { method: "POST", body: new FormData(form) })
        .then(function (res) { if (!res.ok) throw new Error("HTTP " + res.status); window.location.href = "booking-received.html"; })
        .catch(function () {
          setMsg("Sorry, your request could not be sent. Please try again in a moment, or call the salon at " + form.getAttribute("data-phone") + ".", "err");
          btn.disabled = false; label.textContent = old;
        });
    });
  }
})();
