/* ============================================================
   Metodologia IFEM — animações de storytelling.
   - GSAP + ScrollTrigger para o reveal das seções (se disponível).
   - IntersectionObserver para contadores, gráficos e infográficas
     (funciona mesmo sem GSAP — degradação graciosa).
   ============================================================ */
(function () {
  "use strict";

  function onReady(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  onReady(function () {
    const hasGSAP = typeof window.gsap !== "undefined" && typeof window.ScrollTrigger !== "undefined";

    // ---------- Reveal das seções (GSAP) ----------
    if (hasGSAP) {
      gsap.registerPlugin(ScrollTrigger);
      const reveals = gsap.utils.toArray("[data-reveal]");
      reveals.forEach(function (el) {
        gsap.set(el, { opacity: 0, y: 42 });
        ScrollTrigger.create({
          trigger: el,
          start: "top 85%",
          once: true,
          onEnter: function () {
            gsap.to(el, { opacity: 1, y: 0, duration: 0.9, ease: "power3.out" });
          },
        });
      });
    }

    // ---------- Barra de progresso de leitura ----------
    const bar = document.getElementById("met-progress-bar");
    if (bar) {
      const onScroll = function () {
        const h = document.documentElement;
        const max = h.scrollHeight - h.clientHeight;
        const pct = max > 0 ? (h.scrollTop || window.pageYOffset) / max * 100 : 0;
        bar.style.width = pct.toFixed(2) + "%";
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }

    // ---------- Navegação por capítulos (dots) ----------
    const navLinks = Array.from(document.querySelectorAll(".met-nav a"));
    const sections = navLinks
      .map(function (a) { return document.querySelector(a.getAttribute("href")); })
      .filter(Boolean);

    navLinks.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        const target = document.querySelector(a.getAttribute("href"));
        if (target) target.scrollIntoView({ behavior: "smooth" });
      });
    });

    if (sections.length && "IntersectionObserver" in window) {
      const navObs = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            const id = "#" + en.target.id;
            navLinks.forEach(function (a) {
              a.classList.toggle("active", a.getAttribute("href") === id);
            });
          }
        });
      }, { rootMargin: "-45% 0px -45% 0px" });
      sections.forEach(function (s) { navObs.observe(s); });
    }

    // ---------- Contadores numéricos ----------
    function animateCount(el) {
      const target = parseFloat(el.getAttribute("data-count")) || 0;
      const dur = 1400;
      const start = performance.now();
      const fmt = new Intl.NumberFormat("pt-BR");
      function step(now) {
        const t = Math.min(1, (now - start) / dur);
        const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
        el.textContent = fmt.format(Math.round(target * eased));
        if (t < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }

    // ---------- Barra de quintis (5 blocos coloridos) ----------
    function buildQuintilBar(host) {
      const cores = ["#d73027", "#fc8d59", "#fee08b", "#91cf60", "#1a9850"];
      cores.forEach(function (c) {
        const i = document.createElement("i");
        i.style.background = c;
        i.style.flex = "0"; // começa colapsado; anima para 1
        host.appendChild(i);
      });
      // anima o preenchimento dos 5 blocos em sequência
      const blocos = host.querySelectorAll("i");
      blocos.forEach(function (b, idx) {
        setTimeout(function () { b.style.flex = "1"; }, 120 * idx);
      });
    }

    // ---------- Efeito tesoura (desenha os traços) ----------
    function drawScissor() {
      ["scissorTop", "scissorBot"].forEach(function (id, idx) {
        const path = document.getElementById(id);
        if (!path || typeof path.getTotalLength !== "function") return;
        const len = path.getTotalLength();
        path.style.strokeDasharray = len;
        path.style.strokeDashoffset = len;
        // força reflow e anima
        path.getBoundingClientRect();
        path.style.transition = "stroke-dashoffset 1.4s ease " + (idx * 0.15) + "s";
        path.style.strokeDashoffset = "0";
      });
    }

    // ---------- Gráfico de densidade (Chart.js) ----------
    function buildDensityChart(canvas) {
      if (typeof window.Chart === "undefined") return;
      // Curva log-normal-ish: pico à esquerda, cauda longa à direita
      // (espelha a distribuição real da receita per capita no Brasil).
      function dens(x) {
        if (x <= 0) return 0;
        const mu = Math.log(22), s = 0.55;
        return Math.exp(-Math.pow(Math.log(x) - mu, 2) / (2 * s * s)) / (x * s);
      }
      const pts = [];
      for (let x = 1; x <= 100; x++) pts.push({ x: x, y: dens(x) });
      const LINE_X = 11; // município subfinanciado (à esquerda do pico)

      const vLine = {
        id: "vline",
        afterDatasetsDraw: function (chart) {
          const xScale = chart.scales.x;
          const area = chart.chartArea;
          const px = xScale.getPixelForValue(LINE_X);
          const ctx = chart.ctx;
          ctx.save();
          ctx.beginPath();
          ctx.moveTo(px, area.top);
          ctx.lineTo(px, area.bottom);
          ctx.lineWidth = 3;
          ctx.strokeStyle = "#e23b3b";
          ctx.stroke();
          ctx.fillStyle = "#e23b3b";
          ctx.font = "600 12px Inter, sans-serif";
          ctx.fillText("um município", px + 8, area.top + 14);
          ctx.restore();
        },
      };

      const ctx = canvas.getContext("2d");
      const grad = ctx.createLinearGradient(0, 0, 0, 180);
      grad.addColorStop(0, "rgba(25,70,133,.35)");
      grad.addColorStop(1, "rgba(25,70,133,.02)");

      new Chart(ctx, {
        type: "line",
        data: {
          datasets: [{
            data: pts,
            borderColor: "#194685",
            borderWidth: 3,
            fill: true,
            backgroundColor: grad,
            tension: 0.45,
            pointRadius: 0,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 1400, easing: "easeOutCubic" },
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: {
            x: { type: "linear", min: 0, max: 100, display: false },
            y: { display: false, min: 0 },
          },
        },
        plugins: [vLine],
      });
    }

    // ---------- Dispara as animações "uma vez" quando entram na tela ----------
    function whenVisible(el, fn) {
      if (!el) return;
      if (!("IntersectionObserver" in window)) { fn(); return; }
      const obs = new IntersectionObserver(function (entries, observer) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { fn(); observer.disconnect(); }
        });
      }, { threshold: 0.35 });
      obs.observe(el);
    }

    document.querySelectorAll("[data-count]").forEach(function (el) {
      whenVisible(el, function () { animateCount(el); });
    });
    const qbar = document.getElementById("quintilBar");
    whenVisible(qbar, function () { buildQuintilBar(qbar); });
    whenVisible(document.querySelector(".met-scissor"), drawScissor);
    const dchart = document.getElementById("densityChart");
    whenVisible(dchart, function () { buildDensityChart(dchart); });
  });
})();
