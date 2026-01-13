// ifem/static/ifem/js/ifem.js

/**
 * Inicializa animações suaves de entrada das seções na landing do IFEM.
 * Usa IntersectionObserver quando disponível e faz um fallback simples
 * adicionando as classes direto em navegadores mais antigos.
 */
(function () {
  // Garante que o script só rode depois do DOM pronto
  document.addEventListener('DOMContentLoaded', function () {
    const sections = document.querySelectorAll('.js-section');
    if (!sections.length) {
      return;
    }

    // Se o navegador suportar IntersectionObserver, usamos para animar no scroll
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('is-visible');
              // depois que a seção apareceu uma vez, não precisa observar mais
              observer.unobserve(entry.target);
            }
          });
        },
        {
          // Quando ~30% da seção estiver visível já começa a animação
          threshold: 0.3,
        }
      );

      sections.forEach((section) => observer.observe(section));
    } else {
      // Fallback: em navegadores sem IntersectionObserver, mostra tudo direto
      sections.forEach((section) => section.classList.add('is-visible'));
    }
  });
})();
