// ============================================================
//  Animações suaves da landing IFEM usando GSAP + ScrollTrigger
//  - Entrada do hero (texto primeiro, imagem depois)
//  - Reveals por seção no scroll
//  - Parallax leve em imagens
//  - Animação de citações e CTA
// ============================================================

document.addEventListener("DOMContentLoaded", function () {
  // Se GSAP ou ScrollTrigger não estiverem presentes, não tenta animar
  if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
    return;
  }

  gsap.registerPlugin(ScrollTrigger);

  // Respeita preferência de usuário por menos movimento
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReducedMotion) {
    document.documentElement.classList.add("ifem-reduced-motion");
    return;
  }

  // --------------------------------------------
  // HERO – texto entra primeiro, depois a imagem
  // --------------------------------------------
  const heroTimeline = gsap.timeline({
    defaults: {
      duration: 0.9,
      ease: "power2.out"
    }
  });

  heroTimeline
    .from(".anim-hero-text", {
      y: 36,
      opacity: 0,
      stagger: 0.12
    })
    .from(
      ".anim-hero-image",
      {
        y: 24,
        opacity: 0,
        scale: 0.96,
        duration: 1.0
      },
      "-=0.4" // sobreposição parcial com o texto
    );

  // --------------------------------------------
  // Reveals de seções: texto e imagem
  // --------------------------------------------
  document.querySelectorAll(".ifem-section").forEach(function (section) {
    const textEl = section.querySelector(".anim-section-text");
    const imageEl = section.querySelector(".anim-section-image");

    // Texto da seção
    if (textEl) {
      gsap.fromTo(
        textEl,
        { y: 26, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.9,
          ease: "power2.out",
          scrollTrigger: {
            trigger: section,
            start: "top 75%",
            toggleActions: "play none none reverse"
          }
        }
      );
    }

    // Imagem da seção com reveal + parallax leve
    if (imageEl) {
      // Entrada inicial
      gsap.fromTo(
        imageEl,
        { y: 26, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.9,
          ease: "power2.out",
          scrollTrigger: {
            trigger: section,
            start: "top 70%",
            toggleActions: "play none none reverse"
          }
        }
      );

      // Parallax sutil enquanto o usuário rola a página
      gsap.to(imageEl, {
        y: -40, // deslocamento curto para manter a animação discreta
        ease: "none",
        scrollTrigger: {
          trigger: section,
          start: "top bottom",
          end: "bottom top",
          scrub: true
        }
      });
    }
  });

  // --------------------------------------------
  // Citações – cards entram em sequência
  // --------------------------------------------
  const quoteCards = document.querySelectorAll(".anim-quote-card");
  if (quoteCards.length > 0) {
    gsap.fromTo(
      quoteCards,
      { y: 32, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.9,
        ease: "power2.out",
        stagger: 0.18,
        scrollTrigger: {
          trigger: ".ifem-section-quotes",
          start: "top 75%",
          toggleActions: "play none none reverse"
        }
      }
    );
  }

  // --------------------------------------------
  // CTA final – título, texto e botão
  // --------------------------------------------
  const ctaSection = document.querySelector(".ifem-section-cta");
  if (ctaSection) {
    gsap.fromTo(
      ".ifem-cta",
      { y: 32, opacity: 0 },
      {
        y: 0,
        opacity: 1,
        duration: 0.9,
        ease: "power2.out",
        scrollTrigger: {
          trigger: ctaSection,
          start: "top 80%",
          toggleActions: "play none none reverse"
        }
      }
    );

    // Efeito leve no botão quando a seção entra
    gsap.fromTo(
      ".ifem-cta-button",
      { scale: 0.94 },
      {
        scale: 1,
        duration: 0.5,
        ease: "power1.out",
        scrollTrigger: {
          trigger: ctaSection,
          start: "top 80%",
          toggleActions: "play none none none"
        }
      }
    );
  }
});
