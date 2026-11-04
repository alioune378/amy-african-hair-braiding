/* Amy African Hair Braiding And Boutique — interactions (no dependencies) */
(function () {
  "use strict";
  document.documentElement.classList.add("js");
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- mobile menu: overlay, scroll lock, focus trap, Escape */
  var menu = $("[data-menu]"), openBtn = $("[data-menu-open]"), closeBtn = $("[data-menu-close]");
  if (menu && openBtn) {
    var setMenu = function (open) {
      menu.hidden = !open;
      openBtn.setAttribute("aria-expanded", String(open));
      document.body.classList.toggle("menu-open", open);
      if (open) closeBtn.focus(); else openBtn.focus();
    };
    openBtn.addEventListener("click", function () { setMenu(true); });
    closeBtn.addEventListener("click", function () { setMenu(false); });
    $$("a", menu).forEach(function (a) { a.addEventListener("click", function () { menu.hidden = true; document.body.classList.remove("menu-open"); openBtn.setAttribute("aria-expanded", "false"); }); });
    document.addEventListener("keydown", function (ev) {
      if (menu.hidden) return;
      if (ev.key === "Escape") return setMenu(false);
      if (ev.key === "Tab") {
        var f = $$("a, button", menu), first = f[0], last = f[f.length - 1];
        if (ev.shiftKey && document.activeElement === first) { ev.preventDefault(); last.focus(); }
        else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
      }
    });
    window.addEventListener("resize", function () { if (window.innerWidth >= 1040 && !menu.hidden) setMenu(false); });
    window.addEventListener("pageshow", function () { menu.hidden = true; document.body.classList.remove("menu-open"); });
  }

  /* ---------- mobile booking bar: shown after the hero; hidden over the form, the footer and a playing video */
  var bar = $("[data-mbar]");
  if (bar) {
    var hide = $$("#book, [data-foot]");
    var update = function () {
      var vh = window.innerHeight, show = window.scrollY > vh * 0.6;
      hide.forEach(function (el) { var r = el.getBoundingClientRect(); if (r.top < vh && r.bottom > 0) show = false; });
      $$(".reel.is-embedded .reel-frame").forEach(function (el) { var r = el.getBoundingClientRect(); if (r.bottom > vh - 90 && r.top < vh) show = false; });
      bar.classList.toggle("is-on", show);
      bar.setAttribute("aria-hidden", String(!show));
      $$("a", bar).forEach(function (a) { a.tabIndex = show ? 0 : -1; });
    };
    var ticking = false;
    window.addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(function () { ticking = false; update(); }); } }, { passive: true });
    window.addEventListener("resize", update);
    document.addEventListener("focusin", function (ev) { if (ev.target.matches && ev.target.matches("input, select, textarea")) { bar.classList.remove("is-on"); } });
    update();
  }

  /* ---------- carousel arrows */
  var car = $("[data-carousel]");
  if (car) {
    var step = function (d) { var c = $(".reel", car); car.scrollBy({ left: d * ((c ? c.offsetWidth : 260) + 16) * 2, behavior: "smooth" }); };
    var p = $("[data-car-prev]"), n = $("[data-car-next]");
    if (p) p.addEventListener("click", function () { step(-1); });
    if (n) n.addEventListener("click", function () { step(1); });
  }

  /* ---------- filters */
  $$("[data-filter-group]").forEach(function (group) {
    var target = $('[data-filter-target="' + group.getAttribute("data-filter-group") + '"]');
    if (!target) return;
    group.addEventListener("click", function (ev) {
      var btn = ev.target.closest("[data-filter]");
      if (!btn) return;
      var v = btn.getAttribute("data-filter");
      $$("[data-filter]", group).forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      $$("[data-cat]", target).forEach(function (card) { card.hidden = !(v === "all" || card.getAttribute("data-cat") === v); });
    });
  });

  /* ---------- lightbox */
  var lb = $("[data-lb]");
  if (lb) {
    var lbImg = $("[data-lb-img]", lb), lastFocus = null;
    var closeLb = function () { lb.hidden = true; lbImg.removeAttribute("src"); document.body.style.overflow = ""; if (lastFocus) lastFocus.focus(); };
    $$("[data-lightbox]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        lastFocus = btn; lbImg.src = btn.getAttribute("data-lightbox"); lbImg.alt = btn.getAttribute("data-alt") || "";
        lb.hidden = false; document.body.style.overflow = "hidden"; $("[data-lb-close]", lb).focus();
      });
    });
    lb.addEventListener("click", function (ev) { if (ev.target === lb || ev.target.closest("[data-lb-close]")) closeLb(); });
    document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !lb.hidden) closeLb(); });
  }
  $$("[data-ba]").forEach(function (frame) {
    var range = $(".ba-range", frame);
    range.addEventListener("input", function () { frame.style.setProperty("--pos", range.value + "%"); });
  });

  /* ---------- videos: nothing from Instagram or TikTok loads until the visitor taps play */
  var openOut = function (url) { window.open(url, "_blank", "noopener"); };
  var fallback = function (reel, url) {
    reel.setAttribute("data-state", "fallback");
    // Not opened automatically (browsers block pop-ups after a delay): the next tap opens the post.
    var st = $("[data-status]", reel); if (st) st.textContent = "Tap to open on " + (reel.getAttribute("data-kind") === "tiktok" ? "TikTok" : "Instagram");
    void url;
  };
  var igState = "idle", igWait = [];
  var loadIg = function (cb) {
    if (igState === "ready") return cb(true);
    if (igState === "failed") return cb(false);
    igWait.push(cb);
    if (igState === "loading") return;
    igState = "loading";
    var s = document.createElement("script");
    s.async = true; s.src = "https://www.instagram.com/embed.js";
    s.onload = function () { igState = "ready"; igWait.splice(0).forEach(function (f) { f(true); }); };
    s.onerror = function () { igState = "failed"; igWait.splice(0).forEach(function (f) { f(false); }); };
    document.body.appendChild(s);
  };
  var playIg = function (reel) {
    var url = reel.getAttribute("data-permalink"), box = $("[data-embed]", reel), st = $("[data-status]", reel);
    if (st) st.textContent = "Loading…";
    var bq = document.createElement("blockquote");
    bq.className = "instagram-media"; bq.setAttribute("data-instgrm-permalink", url); bq.setAttribute("data-instgrm-version", "14");
    box.appendChild(bq);
    loadIg(function (ok) {
      if (!ok || !window.instgrm) { box.innerHTML = ""; return fallback(reel, url); }
      window.instgrm.Embeds.process();
      var tries = 0, t = setInterval(function () {
        tries++;
        if (box.querySelector("iframe")) { clearInterval(t); reel.classList.add("is-embedded"); reel.setAttribute("data-state", "embedded"); }
        else if (tries > 20) { clearInterval(t); box.innerHTML = ""; fallback(reel, url); }
      }, 400);
    });
  };
  var playTt = function (reel) {
    var vid = reel.getAttribute("data-vid"), url = reel.getAttribute("data-url"), st = $("[data-status]", reel);
    var render = function (id) {
      var f = document.createElement("iframe");
      f.src = "https://www.tiktok.com/player/v1/" + id + "?music_info=0&description=0&rel=0&autoplay=1&loop=0";
      f.title = "TikTok video from " + document.title.split("|")[0];
      f.setAttribute("allow", "autoplay; fullscreen; encrypted-media; picture-in-picture");
      f.setAttribute("allowfullscreen", "");
      f.style.cssText = "position:absolute;inset:0;width:100%;height:100%;border:0";
      var box = $("[data-embed]", reel); box.innerHTML = ""; box.appendChild(f);
      reel.classList.add("is-embedded"); reel.setAttribute("data-state", "embedded");
    };
    if (vid) return render(vid);
    if (st) st.textContent = "Loading…";
    if (!window.fetch) return fallback(reel, url);
    fetch("https://www.tiktok.com/oembed?url=" + encodeURIComponent(url))
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) {
        var m = /data-video-id="(\d+)"/.exec(d.html || "") || /video\/(\d+)/.exec(d.html || "");
        var id = (m && m[1]) || d.embed_product_id;
        if (!id) throw 0;
        reel.setAttribute("data-vid", id); render(id);
      })
      .catch(function () { fallback(reel, url); });
  };
  $$("[data-load]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var reel = btn.closest(".reel"), state = reel.getAttribute("data-state");
      if (state === "fallback") return openOut(reel.getAttribute("data-permalink") || reel.getAttribute("data-url"));
      if (state) return;
      reel.setAttribute("data-state", "loading");
      if (reel.getAttribute("data-kind") === "tiktok") playTt(reel); else playIg(reel);
    });
  });
  document.addEventListener("play", function (ev) {
    if (ev.target.tagName !== "VIDEO") return;
    $$("video").forEach(function (v) { if (v !== ev.target && !v.paused) v.pause(); });
  }, true);

  /* ---------- booking form */
  var form = $("[data-book]");
  if (form) {
    var params = new URLSearchParams(location.search);
    var style = params.get("style"), sel = $("#b-style", form);
    if (style && sel && $$("option", sel).some(function (o) { return o.value === style; })) sel.value = style;
    var d = $("#b-date", form);
    if (d) { var t = new Date(); t.setMinutes(t.getMinutes() - t.getTimezoneOffset()); d.min = t.toISOString().slice(0, 10); }
    var msg = $("[data-msg]", form), btn = $("[data-submit]", form);
    var setMsg = function (text, kind) { msg.textContent = text; msg.className = "form-msg" + (kind ? " " + kind : ""); };
    var MAX = 8 * 1024 * 1024;
    var MSG = { name: "Please enter your name.", phone: "Please enter a phone number we can call or text.", style: "Please choose a hairstyle.",
      date: "Please choose a date from today onwards.", time: "Please choose a time of day." };
    var setErr = function (f, text) {
      f.setAttribute("aria-invalid", text ? "true" : "false");
      var p = document.getElementById(f.id + "-err"); if (p) p.textContent = text || "";
    };
    $$("input, select, textarea", form).forEach(function (f) {
      f.addEventListener("input", function () { if (f.getAttribute("aria-invalid") === "true" && f.checkValidity()) setErr(f, ""); });
      f.addEventListener("change", function () { if (f.getAttribute("aria-invalid") === "true" && f.checkValidity()) setErr(f, ""); });
    });
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      setMsg("");
      var bad = null;
      $$("input, select, textarea", form).forEach(function (f) {
        if (f.type === "hidden" || f.name === "company" || f.type === "file") return;
        var ok = f.checkValidity();
        setErr(f, ok ? "" : (MSG[f.name] || "Please check this field."));
        if (!ok && !bad) bad = f;
      });
      var file = $("#b-photo", form);
      if (file && file.files[0]) {
        var fl = file.files[0], okType = /^image\//.test(fl.type || "image/") || /\.(heic|heif)$/i.test(fl.name);
        if (fl.size > MAX || !okType) { setErr(file, fl.size > MAX ? "This photo is larger than 8 MB. Please choose a smaller one." : "Please choose an image file."); if (!bad) bad = file; }
        else setErr(file, "");
      }
      if (bad) { setMsg("Please check the highlighted fields.", "err"); bad.focus(); return; }
      btn.disabled = true;
      var label = btn.querySelector("span"), old = label.textContent;
      label.textContent = "Sending…";
      fetch("/", { method: "POST", body: new FormData(form) })
        .then(function (res) {
          if (!res.ok) throw new Error("HTTP " + res.status);
          window.location.href = "booking-received.html";
        })
        .catch(function () {
          setMsg("Sorry, your request could not be sent. Please try again, or call us at " + form.getAttribute("data-phone") + ".", "err");
          btn.disabled = false; label.textContent = old;
        });
    });
  }
})();
