gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Inicializa Gráficos (Decis/Quintis)
    if (document.getElementById('bar-display')) {
        updateMethodology('quintil');
    }

    // 2. Animação da Barra de Navegação
    const nav = document.querySelector('.story-nav');
    if (nav) {
        const toggleNav = () => {
            if (window.scrollY > 50) { 
                nav.classList.add('visible');
            } else {
                nav.classList.remove('visible');
            }
        };

        window.addEventListener('scroll', toggleNav);
        
        toggleNav();
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

    // 4. Animação dos Gráficos de Barra (Problema)
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

    // ======================================================================
    // Gráfico de Pizza SVG (Receitas)
    // ======================================================================
    const pieContainer = document.querySelector('.pie-chart-container');
    if (pieContainer) {
        const tlPie = gsap.timeline({
            scrollTrigger: {
                trigger: pieContainer,
                start: "top 80%", 
                toggleActions: "play none none reverse"
            }
        });

        // 1. Anima o desenho do círculo vermelho
        const progressCircle = pieContainer.querySelector('.circle-progress');
        const targetOffset = progressCircle.getAttribute('data-offset');
        
        tlPie.to(progressCircle, { 
            strokeDashoffset: targetOffset,
            duration: 2,
            ease: "power4.out" 
        }, 0);

        // 2. Anima os contadores numéricos
        pieContainer.querySelectorAll('.pie-counter').forEach(counter => {
            const targetVal = parseInt(counter.getAttribute('data-target'));
            let proxy = { val: 0 };
            
            tlPie.to(proxy, {
                val: targetVal,
                duration: 2,
                ease: "power4.out",
                onUpdate: function() {
                    counter.innerText = Math.floor(this.targets()[0].val);
                }
            }, 0);
        });

        // 3. Animação de entrada do container
        tlPie.from(pieContainer, {
            y: 30,
            opacity: 0,
            duration: 0.8,
            ease: "power2.out"
        }, 0);
    }

    // ======================================================================
    // ANIMAÇÃO: Gráficos de População (Barras Laterais - Coluna Direita)
    // ======================================================================
    const popGroups = document.querySelectorAll('.pop-chart-group');
    popGroups.forEach(group => {
        gsap.to(group.querySelectorAll('.pop-bar'), {
            width: function(i, target) {
                return target.getAttribute('data-width');
            },
            duration: 1.5,
            ease: "power2.out",
            stagger: 0.2, 
            scrollTrigger: {
                trigger: group,
                start: "top 85%",
                toggleActions: "play none none reverse"
            }
        });
    });
});

// --- Scroll Suave (Instantâneo) ---
window.scrollToId = function(id) {
    const navHeight = 80; 
    
    // Mata tweens anteriores para evitar conflito
    gsap.killTweensOf(window);

    gsap.to(window, {
        duration: 0.8, 
        scrollTo: { y: `#${id}`, offsetY: navHeight },
        ease: "expo.out",
        overwrite: "auto"
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
    
    const cardWidth = cards[0].offsetWidth + 30; 
    track.parentElement.scrollTo({
        left: currentSlide * cardWidth,
        behavior: 'smooth'
    });
};

// ======================================================================
    // Lógica do Botão "Saiba Mais" (Expansível + Scroll Automático)
    // ======================================================================
    const expandButtons = document.querySelectorAll('.btn-read-more');

    expandButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const content = this.nextElementSibling;
            const isExpanded = this.classList.contains('active');
            const spanText = this.querySelector('.btn-text');

            if (isExpanded) {
                // Fechar
                this.classList.remove('active');
                this.setAttribute('aria-expanded', 'false');
                content.style.maxHeight = null;
                spanText.textContent = "Saiba mais";
            } else {
                // Abrir
                this.classList.add('active');
                this.setAttribute('aria-expanded', 'true');
                content.style.maxHeight = content.scrollHeight + "px";
                spanText.textContent = "Mostrar menos";

                // Scroll suave para centralizar o texto ---
                setTimeout(() => {
                    content.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'center' 
                    });
                }, 30); 
            }
        });
    });