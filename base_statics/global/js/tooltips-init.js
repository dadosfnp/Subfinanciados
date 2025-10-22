// static/global/js/tooltips-init.js
(function () {
  function initTooltips() {
    // espera o Bootstrap estar carregado
    if (!window.bootstrap || !bootstrap.Tooltip) {
      setTimeout(initTooltips, 60);
      return;
    }

    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
      // evita tooltip NATIVE do browser: move o title p/ data-bs-title
      const t = el.getAttribute('title');
      if (t) {
        el.setAttribute('data-bs-title', t);
        el.removeAttribute('title');
      }

      // inicializa com container body p/ não cortar
      new bootstrap.Tooltip(el, {
        container: 'body',
        boundary: 'window',
        html: el.getAttribute('data-bs-html') === 'true',
        // classe custom pra estilizar sem briga com outros tooltips
        customClass: 'fnp-tooltip'
      });
    });
  }

  // roda mesmo se o script for carregado depois do DOMContentLoaded
  if (document.readyState === 'complete') initTooltips();
  else window.addEventListener('load', initTooltips);
})();
