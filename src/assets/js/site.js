/* Amy African Hair Braiding And Boutique — interactions (no dependencies) */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.add("js");
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- mobile menu */
  var menuBtn = $("[data-menu]"), nav = $("[data-nav]");
  if (menuBtn && nav) {
    var setMenu = function (open) {
      menuBtn.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("open", open);
      document.body.classList.toggle("menu-open", open);
    };
    menuBtn.addEventListener("click", function () { setMenu(menuBtn.getAttribute("aria-expanded") !== "true"); });
    document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") setMenu(false); });
    $$("a", nav).forEach(function (a) { a.addEventListener("click", function () { setMenu(false); }); });
  }

  /* ---------- reveal on scroll */
  var reveals = $$(".reveal");
  if ("IntersectionObserver" in window) {
    var ro = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); ro.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    reveals.forEach(function (el) { ro.observe(el); });
  } else { reveals.forEach(function (el) { el.classList.add("in"); }); }

  /* ---------- filters (services and gallery) */
  $$("[data-filter-group]").forEach(function (group) {
    var target = $('[data-filter-target="' + group.getAttribute("data-filter-group") + '"]');
    if (!target) return;
    group.addEventListener("click", function (ev) {
      var btn = ev.target.closest("[data-filter]");
      if (!btn) return;
      var v = btn.getAttribute("data-filter");
      $$("[data-filter]", group).forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      $$("[data-cat]", target).forEach(function (card) {
        card.hidden = !(v === "all" || card.getAttribute("data-cat") === v);
        if (!card.hidden) card.classList.add("in");
      });
    });
  });

  /* ---------- lightbox */
  var lb = $("[data-lb]");
  if (lb) {
    var lbImg = $("[data-lb-img]", lb), lastFocus = null;
    var closeLb = function () { lb.hidden = true; lbImg.removeAttribute("src"); document.body.style.overflow = ""; if (lastFocus) lastFocus.focus(); };
    $$("[data-lightbox]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        lastFocus = btn;
        lbImg.src = btn.getAttribute("data-lightbox");
        lbImg.alt = btn.getAttribute("data-alt") || "";
        lb.hidden = false; document.body.style.overflow = "hidden";
        $("[data-lb-close]", lb).focus();
      });
    });
    lb.addEventListener("click", function (ev) { if (ev.target === lb || ev.target.closest("[data-lb-close]")) closeLb(); });
    document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !lb.hidden) closeLb(); });
  }

  /* ---------- before / after slider */
  $$("[data-ba]").forEach(function (frame) {
    var range = $(".ba-range", frame);
    range.addEventListener("input", function () { frame.style.setProperty("--pos", range.value + "%"); });
  });

  /* ---------- videos: only one plays at a time */
  document.addEventListener("play", function (ev) {
    if (ev.target.tagName !== "VIDEO") return;
    $$("video").forEach(function (v) { if (v !== ev.target && !v.paused) v.pause(); });
  }, true);

  /* ---------- TikTok videos: official player when the video id is known or can be looked up; else a link */
  var tts = $$('.reel[data-kind="tiktok"]');
  if (tts.length) {
    var ttRender = function (reel, vid) {
      var box = $("[data-embed]", reel), status = $("[data-status]", reel);
      var f = document.createElement("iframe");
      f.src = "https://www.tiktok.com/player/v1/" + vid + "?music_info=0&description=0&rel=0&autoplay=0&loop=0";
      f.title = "TikTok video from Amy African Hair Braiding";
      f.setAttribute("allow", "fullscreen; encrypted-media; picture-in-picture");
      f.setAttribute("allowfullscreen", "");
      f.setAttribute("loading", "lazy");
      f.style.cssText = "position:absolute;inset:0;width:100%;height:100%;border:0";
      var done = false;
      f.addEventListener("load", function () { done = true; reel.classList.add("is-embedded"); reel.setAttribute("data-state", "embedded"); }, { once: true });
      box.innerHTML = ""; box.appendChild(f);
      setTimeout(function () {
        if (!done) { reel.setAttribute("data-state", "fallback"); box.innerHTML = ""; if (status) status.textContent = "Watch on TikTok"; }
      }, 15000);
    };
    var ttEmbed = function (reel) {
      if (reel.getAttribute("data-state")) return;
      reel.setAttribute("data-state", "loading");
      var status = $("[data-status]", reel);
      if (status) status.textContent = "Loading video…";
      var vid = reel.getAttribute("data-vid");
      if (vid) return ttRender(reel, vid);
      var url = reel.getAttribute("data-url");
      if (!window.fetch) { reel.setAttribute("data-state", "fallback"); if (status) status.textContent = "Watch on TikTok"; return; }
      fetch("https://www.tiktok.com/oembed?url=" + encodeURIComponent(url))
        .then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function (d) {
          var m = /data-video-id="(\d+)"/.exec(d.html || "") || /video\/(\d+)/.exec(d.html || "");
          var id = (m && m[1]) || d.embed_product_id;
          if (!id) throw 0;
          if (d.author_unique_id) reel.setAttribute("data-handle", d.author_unique_id);
          ttRender(reel, id);
        })
        .catch(function () { reel.setAttribute("data-state", "fallback"); if (status) status.textContent = "Watch on TikTok"; });
    };
    if ("IntersectionObserver" in window) {
      var tio = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { ttEmbed(en.target); tio.unobserve(en.target); } });
      }, { rootMargin: "300px 0px" });
      tts.forEach(function (r) { tio.observe(r); });
    } else { tts.forEach(ttEmbed); }
  }

  /* ---------- Instagram reels: official embeds, lazy-loaded, with a link fallback */
  var reels = $$('.reel[data-kind="instagram"]');
  if (reels.length) {
    var scriptState = "idle", waiting = [];
    var loadScript = function (cb) {
      if (scriptState === "ready") return cb(true);
      if (scriptState === "failed") return cb(false);
      waiting.push(cb);
      if (scriptState === "loading") return;
      scriptState = "loading";
      var s = document.createElement("script");
      s.async = true;
      s.src = "https://www.instagram.com/embed.js";
      s.onload = function () { scriptState = "ready"; waiting.splice(0).forEach(function (f) { f(true); }); };
      s.onerror = function () { scriptState = "failed"; waiting.splice(0).forEach(function (f) { f(false); }); };
      document.body.appendChild(s);
    };
    var embed = function (reel) {
      var url = reel.getAttribute("data-permalink");
      var box = $("[data-embed]", reel), status = $("[data-status]", reel);
      if (!url || !box || reel.getAttribute("data-state")) return;
      reel.setAttribute("data-state", "loading");
      if (status) status.textContent = "Loading video…";
      var bq = document.createElement("blockquote");
      bq.className = "instagram-media";
      bq.setAttribute("data-instgrm-permalink", url);
      bq.setAttribute("data-instgrm-version", "14");
      var a = document.createElement("a");
      a.href = url; a.target = "_blank"; a.rel = "noopener"; a.textContent = "View this video on Instagram";
      bq.appendChild(a);
      box.appendChild(bq);
      loadScript(function (ok) {
        var fail = function () {
          reel.setAttribute("data-state", "fallback");
          box.innerHTML = "";
          if (status) status.textContent = "Watch on Instagram";
        };
        if (!ok || !window.instgrm) return fail();
        window.instgrm.Embeds.process();
        var tries = 0;
        var check = setInterval(function () {
          tries++;
          var frame = box.querySelector("iframe");
          if (frame) {
            clearInterval(check);
            frame.addEventListener("load", function () { reel.classList.add("is-embedded"); reel.setAttribute("data-state", "embedded"); }, { once: true });
            setTimeout(function () { if (box.querySelector("iframe")) { reel.classList.add("is-embedded"); reel.setAttribute("data-state", "embedded"); } }, 2500);
          } else if (tries > 24) { clearInterval(check); fail(); }
        }, 500);
      });
    };
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) { embed(en.target); io.unobserve(en.target); } });
      }, { rootMargin: "200px 0px" });
      reels.forEach(function (r) { io.observe(r); });
    }
  }

  /* ---------- booking form */
  var form = $("[data-book]");
  if (form) {
    var params = new URLSearchParams(location.search);
    var style = params.get("style"), sel = $("#b-style", form);
    if (style && sel) {
      var match = $$("option", sel).filter(function (o) { return o.value === style; })[0];
      if (match) sel.value = style;
    }
    var d = $("#b-date", form);
    if (d) { var t = new Date(); t.setMinutes(t.getMinutes() - t.getTimezoneOffset()); d.min = t.toISOString().slice(0, 10); }
    var msg = $("[data-msg]", form), btn = $("[data-submit]", form);
    var setMsg = function (text, kind) { msg.textContent = text; msg.className = "form-msg" + (kind ? " " + kind : ""); };
    var MAX = 8 * 1024 * 1024;

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      setMsg("");
      var bad = null;
      $$("input, select, textarea", form).forEach(function (f) {
        if (f.type === "hidden" || f.name === "company") return;
        var ok = f.checkValidity();
        f.setAttribute("aria-invalid", ok ? "false" : "true");
        if (!ok && !bad) bad = f;
      });
      var file = $("#b-photo", form);
      if (file && file.files[0] && file.files[0].size > MAX) {
        file.setAttribute("aria-invalid", "true");
        if (!bad) bad = file;
        setMsg("The photo is larger than 8 MB. Please choose a smaller image.", "err");
        bad.focus(); return;
      }
      if (bad) { setMsg("Please complete the highlighted fields.", "err"); bad.focus(); return; }

      btn.disabled = true;
      var label = btn.querySelector("span"), old = label.textContent;
      label.textContent = "Sending…";
      fetch("/", { method: "POST", body: new FormData(form) })
        .then(function (res) {
          if (!res.ok) throw new Error("HTTP " + res.status);
          form.reset();
          setMsg("Thank you! Your appointment request has been received. Our team will contact you to confirm availability.", "ok");
          msg.scrollIntoView({ block: "center", behavior: "smooth" });
        })
        .catch(function () {
          setMsg("Sorry, your request could not be sent. Please call us at " + form.getAttribute("data-phone") + " or try again.", "err");
        })
        .then(function () { btn.disabled = false; label.textContent = old; });
    });
  }
})();
