gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Inicializa Gráficos (Decis/Quintis)
    if (document.getElementById('bar-display')) {
        updateMethodology('quintil');
    }

    // 2. Animação da Barra de Navegação
    const nav = document.querySelector('.story-nav');
    if (nav) {
        ScrollTrigger.create({
            trigger: ".hero-section",
            start: "bottom top", 
            onEnter: () => nav.classList.add('visible'),
            onLeaveBack: () => nav.classList.remove('visible')
        });
    }

    // 3. Highlight dos Itens do Menu
    const sections = ['problema', 'intro', 'plataforma', 'noticias'];
    
    sections.forEach((id, index) => {
        const section = document.getElementById(id);
        const navItem = document.getElementById(`nav-${id}`);
        
        if (section && navItem) {
            ScrollTrigger.create({
                trigger: section,
                start: "top 60%", 
                end: "bottom 60%",
                onToggle: (self) => {
                    if (self.isActive) {
                        document.querySelectorAll('.story-item').forEach(el => el.classList.remove('active'));
                        navItem.classList.add('active');
                        
                        const progress = ((index + 1) / sections.length) * 100;
                        gsap.to('#reading-progress', { width: `${progress}%`, duration: 0.3 });
                    }
                }
            });
        }
    });

    // 4. Animação dos Gráficos de Barra
    const chartRows = document.querySelectorAll('.chart-row');
    chartRows.forEach((row) => {
        const bar = row.querySelector('.bar');
        const counter = row.querySelector('.counter');
        if (!bar || !counter) return;

        const widthVal = bar.getAttribute('data-width');
        const numVal = parseFloat(counter.getAttribute('data-target'));

        gsap.fromTo(bar, 
            { width: "0%" }, 
            { 
                width: widthVal, 
                duration: 1.5, 
                ease: "power2.out",
                scrollTrigger: { trigger: row, start: "top 85%" }
            }
        );

        let proxy = { val: 0 };
        gsap.to(proxy, {
            val: numVal,
            duration: 2,
            scrollTrigger: { trigger: row, start: "top 85%" },
            onUpdate: function() {
                counter.innerText = this.targets()[0].val.toFixed(1).replace('.', ',');
            }
        });
    });
});

// --- Scroll Suave (Instantâneo) ---
window.scrollToId = function(id) {
    const navHeight = 80; 
    gsap.to(window, {
        duration: 0.8, // Duração total reduzida para ficar mais ágil
        scrollTo: { y: `#${id}`, offsetY: navHeight },
        ease: "expo.out" // Velocidade máxima já no primeiro frame (sem aceleração inicial)
    });
};

// --- Lógica Quintis/Decis ---
window.updateMethodology = function(mode) {
    const container = document.getElementById('bar-display');
    const caption = document.getElementById('caption-dynamic');
    const btnQuintil = document.getElementById('btn-quintil');
    const btnDecil = document.getElementById('btn-decil');

    if (!container) return;

    if (mode === 'quintil') {
        btnQuintil?.classList.add('active'); btnDecil?.classList.remove('active');
        if(caption) caption.innerText = "2. Dividimos em 5 grupos iguais (Quintis)";
        renderBars(container, 5, 'q');
    } else {
        btnQuintil?.classList.remove('active'); btnDecil?.classList.add('active');
        if(caption) caption.innerText = "2. Dividimos em 10 grupos iguais (Decis)";
        renderBars(container, 10, 'd');
    }
};

function renderBars(container, count, prefix) {
    container.innerHTML = '';
    const percentText = count === 5 ? '20%' : '10%'; 

    for (let i = 1; i <= count; i++) {
        const div = document.createElement('div');
        div.className = `slice ${prefix}-${i}`; 
        
        if (count === 5 || window.innerWidth > 600) {
            div.innerHTML = `<span>${percentText}</span>`;
        }
        
        container.appendChild(div);
        setTimeout(() => div.classList.add('visible'), i * 40);
    }
}

// --- Carrossel da Plataforma ---
let currentSlide = 0;
window.moveSlide = function(direction) {
    const track = document.getElementById('track');
    const cards = document.querySelectorAll('.platform-card');
    if (!track || !cards.length) return;
    
    currentSlide += direction;
    if (currentSlide < 0) currentSlide = cards.length - 1;
    if (currentSlide >= cards.length) currentSlide = 0;
    
    // Move usando scroll nativo para compatibilidade
    const cardWidth = cards[0].offsetWidth + 30; // largura + gap
    track.parentElement.scrollTo({
        left: currentSlide * cardWidth,
        behavior: 'smooth'
    });
};