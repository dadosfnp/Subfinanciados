// ==========================================================
// IFEM Landing – JS Otimizado (sem perder nenhuma função)
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {

  // ========================================================
  // OBSERVER MANAGER — controla todos observers em um lugar
  // ========================================================
  const ObserverManager = {
    observers: {},

    create(name, callback, options = {}) {
      this.observers[name] = new IntersectionObserver(callback, options);
      return this.observers[name];
    },

    use(name) {
      return this.observers[name];
    }
  };


  // ========================================================
  // 1) Animação principal das seções (.js-section)
  // ========================================================

  const jsSections = document.querySelectorAll(".js-section");

  ObserverManager.create(
    "sectionAppear",
    (entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.30 }
  );

  jsSections.forEach(sec => ObserverManager.use("sectionAppear").observe(sec));


  // ========================================================
  // 2) Fade + subida suave (.js-section.visible)
  // ========================================================

  ObserverManager.create(
    "sectionScrollReveal",
    (entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.18 }
  );

  jsSections.forEach(sec =>
    ObserverManager.use("sectionScrollReveal").observe(sec)
  );


  // ========================================================
  // 3) Cards (ifem-card) revelando ao entrar na tela
  // ========================================================

  const cards = document.querySelectorAll(".ifem-card");

  ObserverManager.create(
    "cardReveal",
    (entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.18 }
  );

  cards.forEach(card =>
    ObserverManager.use("cardReveal").observe(card)
  );


  // ========================================================
  // 4) Fade entre seções (.ifem-section) — storytelling
  // ========================================================

  ObserverManager.create(
    "fadeSections",
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("fade-in");
        }
      });
    },
    { threshold: 0.4 }
  );

  document.querySelectorAll(".ifem-section").forEach(sec =>
    ObserverManager.use("fadeSections").observe(sec)
  );


  // ========================================================
  // 5) Parallax global (data-parallax)
  // ========================================================

  function parallaxUpdate() {
    const scrollY = window.scrollY || window.pageYOffset;

    document.querySelectorAll("[data-parallax]").forEach(el => {
      const speed = 0.12;
      const offset = scrollY * speed;
      el.style.transform = `translateY(${offset}px)`;
    });
  }

  window.addEventListener("scroll", parallaxUpdate);
  parallaxUpdate();


  // ========================================================
  // 6) Parallax "ativado" (parallax-active)
  // ========================================================

  function parallaxActivation() {
    document.querySelectorAll("[data-parallax]").forEach(el => {
      const rect = el.getBoundingClientRect();
      const visible = rect.top < window.innerHeight && rect.bottom > 0;
      el.classList.toggle("parallax-active", visible);
    });
  }

  window.addEventListener("scroll", parallaxActivation);
  window.addEventListener("load", parallaxActivation);
});
