/**
 * IFEM Carousel
 * - Carrossel com dots e setas
 * - Modal de imagem com navegação
 */

(function () {

  let currentImages = [];
  let currentIndex = 0;

  function initCarousel(root) {
    const track = root.querySelector(".ifem-carousel-track");
    const slides = Array.from(root.querySelectorAll(".ifem-carousel-slide"));
    const dots = Array.from(root.querySelectorAll(".ifem-dot"));
    const prevBtn = root.querySelector(".ifem-carousel-prev");
    const nextBtn = root.querySelector(".ifem-carousel-next");

    if (!track || slides.length === 0) return;

    let index = 0;
    const total = slides.length;

    currentImages = slides.map(slide =>
      slide.querySelector("img")
    );

    function update() {
      track.style.transform = `translateX(-${index * 100}%)`;
      dots.forEach((dot, i) => {
        dot.classList.toggle("is-active", i === index);
      });
    }

    function goTo(i) {
      index = Math.max(0, Math.min(i, total - 1));
      update();
    }

    function next() {
      index = (index + 1) % total;
      update();
    }

    function prev() {
      index = (index - 1 + total) % total;
      update();
    }

    dots.forEach((dot, i) => {
      dot.addEventListener("click", () => goTo(i));
    });

    nextBtn?.addEventListener("click", next);
    prevBtn?.addEventListener("click", prev);

    slides.forEach((slide, i) => {
      slide.addEventListener("click", () => {
        currentIndex = i;
        openMediaModal();
      });
    });

    update();
  }

  /* ===============================
     Modal
  =============================== */

  const modal = document.getElementById("ifemMediaModal");
  const modalImg = modal?.querySelector(".ifem-media-modal-img");
  const modalPrev = modal?.querySelector(".ifem-media-modal-prev");
  const modalNext = modal?.querySelector(".ifem-media-modal-next");

  function openMediaModal() {
    if (!modal || !modalImg) return;

    const img = currentImages[currentIndex];
    if (!img) return;

    modalImg.src = img.src;
    modalImg.alt = img.alt || "";

    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeMediaModal() {
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    modalImg.src = "";
    document.body.style.overflow = "";
  }

  function showNext() {
    currentIndex = (currentIndex + 1) % currentImages.length;
    openMediaModal();
  }

  function showPrev() {
    currentIndex =
      (currentIndex - 1 + currentImages.length) % currentImages.length;
    openMediaModal();
  }

  modalPrev?.addEventListener("click", showPrev);
  modalNext?.addEventListener("click", showNext);

  modal?.addEventListener("click", (event) => {
    if (
      event.target.hasAttribute("data-close") ||
      event.target.classList.contains("ifem-media-modal-backdrop")
    ) {
      closeMediaModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (!modal.classList.contains("is-open")) return;

    if (event.key === "Escape") closeMediaModal();
    if (event.key === "ArrowRight") showNext();
    if (event.key === "ArrowLeft") showPrev();
  });

  document.addEventListener("DOMContentLoaded", () => {
    document
      .querySelectorAll(".ifem-carousel")
      .forEach(initCarousel);
  });

})();

/* =========================================================
   IFEM Carousel – Autoplay
========================================================= */

document.querySelectorAll('.ifem-carousel[data-autoplay="true"]').forEach((carousel) => {
  const track = carousel.querySelector('.ifem-carousel-track');
  const slides = carousel.querySelectorAll('.ifem-carousel-slide');
  const dots = carousel.querySelectorAll('.ifem-dot');

  if (!track || slides.length <= 1) return;

  let index = 0;
  let interval = null;
  const delay = 4500; // suave, não agressivo

  function goToSlide(i) {
    index = (i + slides.length) % slides.length;
    track.style.transform = `translateX(-${index * 100}%)`;

    dots.forEach((dot, d) => {
      dot.classList.toggle('is-active', d === index);
    });
  }

  function startAutoplay() {
    interval = setInterval(() => {
      goToSlide(index + 1);
    }, delay);
  }

  function stopAutoplay() {
    clearInterval(interval);
  }

  // interação pausa autoplay
  carousel.addEventListener('mouseenter', stopAutoplay);
  carousel.addEventListener('mouseleave', startAutoplay);

  // dots continuam funcionando
  dots.forEach((dot, i) => {
    dot.addEventListener('click', () => {
      goToSlide(i);
    });
  });

  startAutoplay();
});
