/* ============================================================
   Metodologia IFEM — interações e animações de storytelling.
   Linguagem alinhada à landing (GSAP + ScrollTrigger), com
   scroll fluido (parallax + reveal em lote), donut interativo,
   tabs, "saiba mais", contadores e gráfico de densidade contido.
   Degradação graciosa: sem JS, todo o conteúdo fica visível.
   ============================================================ */
(function () {
  "use strict";

  function onReady(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  onReady(function () {
    const hasGSAP = typeof window.gsap !== "undefined" && typeof window.ScrollTrigger !== "undefined";

    /* ---------- Scroll fluido: parallax + reveal em lote ---------- */
    if (hasGSAP) {
      gsap.registerPlugin(ScrollTrigger);
      if (typeof window.ScrollToPlugin !== "undefined") gsap.registerPlugin(ScrollToPlugin);

      // Parallax sutil das camadas do hero
      document.querySelectorAll("[data-parallax]").forEach(function (el) {
        const depth = parseFloat(el.getAttribute("data-parallax")) || 0.2;
        gsap.to(el, {
          yPercent: depth * 34, ease: "none",
          scrollTrigger: { trigger: ".met-hero", start: "top top", end: "bottom top", scrub: true },
        });
      });

      // Reveal escalonado: elementos que entram juntos sobem em sequência
      const anims = gsap.utils.toArray("[data-anim]");
      gsap.set(anims, { opacity: 0, y: 34 });
      ScrollTrigger.batch("[data-anim]", {
        start: "top 88%",
        onEnter: function (batch) {
          gsap.to(batch, { opacity: 1, y: 0, duration: 0.85, stagger: 0.12, ease: "power3.out", overwrite: true });
        },
      });
    }

    /* ---------- Barra de progresso ---------- */
    const pbar = document.getElementById("met-progress-bar");
    const dots = document.querySelector(".met-dots");
    function onScroll() {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      const y = h.scrollTop || window.pageYOffset;
      if (pbar) pbar.style.width = (max > 0 ? (y / max * 100) : 0).toFixed(2) + "%";
      if (dots) dots.classList.toggle("show", y > window.innerHeight * 0.6);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    /* ---------- Smooth-scroll (cue + dots) ---------- */
    function smoothTo(target) {
      if (!target) return;
      if (hasGSAP && typeof window.ScrollToPlugin !== "undefined") {
        gsap.to(window, { duration: 1.1, scrollTo: { y: target, offsetY: 76 }, ease: "power4.out" });
      } else {
        target.scrollIntoView({ behavior: "smooth" });
      }
    }
    const cue = document.getElementById("heroCue");
    if (cue) cue.addEventListener("click", function (e) {
      e.preventDefault(); smoothTo(document.querySelector(cue.getAttribute("href")));
    });

    /* ---------- Dots: navegação + estado ativo ---------- */
    const dotLinks = Array.from(document.querySelectorAll(".met-dots a"));
    const dotSecs = dotLinks.map(function (a) { return document.querySelector(a.getAttribute("href")); }).filter(Boolean);
    dotLinks.forEach(function (a) {
      a.addEventListener("click", function (e) { e.preventDefault(); smoothTo(document.querySelector(a.getAttribute("href"))); });
    });
    if (dotSecs.length && "IntersectionObserver" in window) {
      const obs = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            const id = "#" + en.target.id;
            dotLinks.forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === id); });
          }
        });
      }, { rootMargin: "-45% 0px -45% 0px" });
      dotSecs.forEach(function (s) { obs.observe(s); });
    }

    /* ---------- "uma vez ao ficar visível" ---------- */
    function whenVisible(el, fn, threshold) {
      if (!el) return;
      if (!("IntersectionObserver" in window)) { fn(); return; }
      const obs = new IntersectionObserver(function (entries, o) {
        entries.forEach(function (en) { if (en.isIntersecting) { fn(); o.disconnect(); } });
      }, { threshold: threshold || 0.3 });
      obs.observe(el);
    }

    /* ---------- Contadores ---------- */
    const fmt = new Intl.NumberFormat("pt-BR");
    function animateCount(el) {
      const target = parseFloat(el.getAttribute("data-count")) || 0;
      const prefix = el.getAttribute("data-prefix") || "";
      const start = performance.now(), dur = 1500;
      function step(now) {
        const t = Math.min(1, (now - start) / dur);
        const e = 1 - Math.pow(1 - t, 3);
        el.textContent = prefix + fmt.format(Math.round(target * e));
        if (t < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }
    document.querySelectorAll("[data-count]").forEach(function (el) {
      whenVisible(el, function () { animateCount(el); });
    });

    /* ---------- Barras (cidades) ---------- */
    document.querySelectorAll("[data-w]").forEach(function (bar) {
      whenVisible(bar, function () {
        requestAnimationFrame(function () { bar.style.transition = "width 1.6s cubic-bezier(.2,.7,.2,1)"; bar.style.width = bar.getAttribute("data-w"); });
      }, 0.6);
    });

    /* ---------- Donut de receitas ---------- */
    const donut = document.getElementById("donut");
    if (donut) {
      const R = 80, C = 2 * Math.PI * R;
      const props = [0.18, 0.62, 0.06, 0.14]; // ilustrativo: transferências dominam
      const segs = donut.querySelectorAll(".met-donut__seg");
      let acc = 0;
      const starts = [];
      props.forEach(function (p) { starts.push(acc); acc += p; });
      whenVisible(donut, function () {
        segs.forEach(function (seg, i) {
          const len = props[i] * C, gap = 2;
          seg.style.strokeDashoffset = (-starts[i] * C).toString();
          requestAnimationFrame(function () { seg.style.strokeDasharray = Math.max(0, len - gap) + " " + (C - len + gap); });
        });
      }, 0.4);
      // hover cruzado legenda <-> segmento, mostrando o número no centro
      const center = document.getElementById("donutCenter");
      const NOMES = ["Impostos & Taxas", "Transferências", "Contribuições", "Outras receitas"];
      const PCT = ["18%", "62%", "6%", "14%"];
      function setCenter(idx) {
        if (!center) return;
        center.innerHTML = (idx == null) ? "<b>25</b><span>fontes</span>"
          : "<b>" + PCT[idx] + "</b><span>" + NOMES[idx] + "</span>";
      }
      function hover(idx, on) {
        segs.forEach(function (seg) {
          const s = seg.getAttribute("data-slice");
          seg.classList.toggle("hot", on && s == idx);
          seg.classList.toggle("dim", on && s != idx);
        });
        setCenter(on ? parseInt(idx, 10) : null);
      }
      document.querySelectorAll(".met-legend li[data-slice]").forEach(function (li) {
        const idx = li.getAttribute("data-slice");
        li.addEventListener("mouseenter", function () { hover(idx, true); });
        li.addEventListener("mouseleave", function () { hover(idx, false); });
      });
      segs.forEach(function (seg) {
        const idx = seg.getAttribute("data-slice");
        seg.addEventListener("mouseenter", function () { hover(idx, true); });
        seg.addEventListener("mouseleave", function () { hover(idx, false); });
      });
    }

    /* ---------- Régua de quantis (muda conforme a aba) ---------- */
    // Paleta RdYlGn (vermelho → amarelo → verde), interpolada para N divisões.
    const STOPS = [[215,48,39],[252,141,89],[254,224,139],[145,207,96],[26,152,80]];
    function corEscala(t) {
      t = Math.max(0, Math.min(1, t));
      const seg = t * (STOPS.length - 1);
      const i = Math.min(STOPS.length - 2, Math.floor(seg));
      const f = seg - i, a = STOPS[i], b = STOPS[i + 1];
      return "rgb(" + Math.round(a[0]+(b[0]-a[0])*f) + "," + Math.round(a[1]+(b[1]-a[1])*f) + "," + Math.round(a[2]+(b[2]-a[2])*f) + ")";
    }
    const qbar = document.getElementById("quintilBar");
    function renderRegua(n) {
      if (!qbar) return;
      qbar.innerHTML = "";
      for (let i = 0; i < n; i++) {
        const el = document.createElement("i");
        el.style.background = corEscala(n === 1 ? 0 : i / (n - 1));
        if (n <= 10) el.textContent = (i + 1); // número do quintil/decil sobre a régua
        qbar.appendChild(el);
      }
      const blocos = qbar.querySelectorAll("i"), total = 420; // entrada em lote (~0,4s)
      blocos.forEach(function (b, idx) {
        setTimeout(function () { b.style.opacity = "1"; b.style.transform = "scaleY(1)"; }, (total / n) * idx);
      });
    }
    const REGUA_N = { q: 5, d: 10, p: 100 };
    whenVisible(qbar, function () { renderRegua(REGUA_N.q); }, 0.35);

    /* ---------- Tabs (quantil/decil/percentil) ---------- */
    const tabHead = document.querySelector(".met-tabs__head");
    if (tabHead) {
      tabHead.querySelectorAll("button").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const tab = btn.getAttribute("data-tab");
          tabHead.querySelectorAll("button").forEach(function (b) { b.classList.toggle("active", b === btn); });
          document.querySelectorAll(".met-tabpane").forEach(function (p) {
            const on = p.getAttribute("data-pane") === tab;
            p.classList.toggle("active", on);
            if (on) { const n = p.querySelector("[data-count]"); if (n) animateCount(n); }
          });
          renderRegua(REGUA_N[tab] || 5); // a régua acompanha a aba
        });
      });
    }

    /* ---------- "Saiba mais" expansível ---------- */
    document.querySelectorAll("[data-more]").forEach(function (btn) {
      const panel = btn.nextElementSibling;
      btn.addEventListener("click", function () {
        const open = btn.getAttribute("aria-expanded") === "true";
        btn.setAttribute("aria-expanded", open ? "false" : "true");
        if (panel) panel.style.maxHeight = open ? null : (panel.scrollHeight + "px");
        if (hasGSAP) setTimeout(function () { ScrollTrigger.refresh(); }, 460);
      });
    });

    /* ---------- Tesoura (desenha os traços) ---------- */
    function drawScissor() {
      ["scTop", "scBot"].forEach(function (id, idx) {
        const path = document.getElementById(id);
        if (!path || typeof path.getTotalLength !== "function") return;
        const len = path.getTotalLength();
        path.style.strokeDasharray = len; path.style.strokeDashoffset = len;
        path.getBoundingClientRect();
        path.style.transition = "stroke-dashoffset 1.5s ease " + (idx * 0.15) + "s";
        path.style.strokeDashoffset = "0";
      });
    }
    whenVisible(document.querySelector(".met-scissor"), drawScissor, 0.4);

    /* ---------- Densidade (Chart.js, contido) ---------- */
    const dcanvas = document.getElementById("densityChart");
    function buildDensity(canvas) {
      if (typeof window.Chart === "undefined") return;
      function dens(x) { if (x <= 0) return 0; const mu = Math.log(22), s = 0.55; return Math.exp(-Math.pow(Math.log(x) - mu, 2) / (2 * s * s)) / (x * s); }
      const pts = []; for (let x = 1; x <= 100; x++) pts.push({ x: x, y: dens(x) });
      const LINE_X = 11;

      // Marcador do município: sombreia a faixa subfinanciada e desenha a linha + rótulo
      // numa cápsula acima da curva (no padding do topo), sem colidir com o pico.
      const marker = {
        id: "marker",
        beforeDatasetsDraw: function (chart) {
          const a = chart.chartArea, px = chart.scales.x.getPixelForValue(LINE_X), ctx = chart.ctx;
          ctx.save(); ctx.fillStyle = "rgba(198,40,40,.05)"; ctx.fillRect(a.left, a.top, px - a.left, a.bottom - a.top); ctx.restore();
        },
        afterDatasetsDraw: function (chart) {
          const a = chart.chartArea, ctx = chart.ctx;
          const px = chart.scales.x.getPixelForValue(LINE_X);
          ctx.save();
          // linha + base
          ctx.beginPath(); ctx.moveTo(px, a.top); ctx.lineTo(px, a.bottom); ctx.lineWidth = 2.5; ctx.strokeStyle = "#c62828"; ctx.stroke();
          ctx.beginPath(); ctx.arc(px, a.bottom, 3.5, 0, Math.PI * 2); ctx.fillStyle = "#c62828"; ctx.fill();
          // cápsula com rótulo no topo (dentro do padding superior)
          const txt = "um município"; ctx.font = "600 12px Inter, sans-serif";
          const w = ctx.measureText(txt).width + 16, h = 22, y = a.top - h - 4;
          let x = px - w / 2; x = Math.max(a.left, Math.min(x, a.right - w));
          ctx.fillStyle = "#c62828"; ctx.beginPath();
          if (ctx.roundRect) ctx.roundRect(x, y, w, h, 7); else ctx.rect(x, y, w, h);
          ctx.fill();
          // ponteiro
          ctx.beginPath(); ctx.moveTo(px - 5, y + h); ctx.lineTo(px + 5, y + h); ctx.lineTo(px, y + h + 5); ctx.closePath(); ctx.fill();
          ctx.fillStyle = "#fff"; ctx.fillText(txt, x + 8, y + 15);
          ctx.restore();
        },
      };
      const ctx = canvas.getContext("2d");
      const grad = ctx.createLinearGradient(0, 0, 0, 220);
      grad.addColorStop(0, "rgba(25,70,133,.28)"); grad.addColorStop(1, "rgba(25,70,133,.02)");
      new Chart(ctx, {
        type: "line",
        data: { datasets: [{ data: pts, borderColor: "#194685", borderWidth: 2.5, fill: true, backgroundColor: grad, tension: 0.45, pointRadius: 0 }] },
        options: {
          responsive: true, maintainAspectRatio: false,
          layout: { padding: { top: 30, left: 2, right: 2 } },
          animation: { duration: 1500, easing: "easeOutCubic" },
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: { x: { type: "linear", min: 0, max: 100, display: false }, y: { display: false, min: 0 } },
        },
        plugins: [marker],
      });
    }
    whenVisible(dcanvas, function () { buildDensity(dcanvas); }, 0.3);

    /* ---------- Escala de portes (barras crescem em sequência) ---------- */
    const portes = document.querySelector(".met-portes");
    whenVisible(portes, function () {
      portes.querySelectorAll(".met-porte i").forEach(function (b, idx) { b.style.transitionDelay = (idx * 0.06) + "s"; });
      portes.classList.add("in");
    }, 0.3);
  });
})();
