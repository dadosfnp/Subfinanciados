// Registra os plugins do GSAP
gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

document.addEventListener("DOMContentLoaded", () => {
    console.log("🚀 IFEM Landing: Stack-Aware Navigation Loaded");

    // 1. Navegação Inteligente (Cálculo de Pilha)
    setupStackNavigation();

    // 2. Gráficos (Mantido)
    setupChartAnimations();

    // 3. Metodologia (Mantido)
    if (document.getElementById('bar-display')) {
        updateMethodology('quintil');
    }
});

// =========================================================
//  MÓDULO DE NAVEGAÇÃO "SANDUÍCHE" (O CORRETOR DE PILHA)
// =========================================================
function setupStackNavigation() {
    document.addEventListener('click', (e) => {
        // Detecta clique em qualquer botão que deva rolar a página
        const trigger = e.target.closest('a[onclick], .scroll-indicator, .sticky-header');
        
        if (trigger) {
            let targetId = null;

            // Tenta pegar o ID do target (suporta data-target ou o onclick antigo)
            if (trigger.dataset.target) {
                targetId = trigger.dataset.target;
            } else {
                const clickAttr = trigger.getAttribute('onclick');
                if (clickAttr) {
                    const match = clickAttr.match(/scrollToSection\(['"](.+)['"]\)/);
                    if (match) targetId = match[1];
                }
            }

            if (targetId) {
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    e.preventDefault();
                    e.stopPropagation();
                    performStackScroll(targetElement);
                }
            }
        }
    });
}

function performStackScroll(targetElement) {
    // 1. Altura do Menu Principal (Fixo)
    const pageHeader = document.querySelector('.page-header');
    const headerHeight = pageHeader ? pageHeader.offsetHeight : 0;

    // 2. Altura da "Pilha" de seções anteriores (Sanduíche)
    // Se a seção A e B ficam grudadas no topo quando leio a C, 
    // preciso descontar a altura delas também.
    let stackOffset = 0;
    
    // Pega todas as seções que possuem cabeçalho sticky
    const allSections = document.querySelectorAll('.book-section');
    
    for (let section of allSections) {
        // Se chegamos na seção alvo, paramos de somar
        if (section === targetElement) break;

        // Se é uma seção anterior, somamos a altura do cabeçalho dela
        const stickyHeader = section.querySelector('.sticky-header');
        if (stickyHeader) {
            stackOffset += stickyHeader.offsetHeight;
        }
    }

    // 3. Offset Total = Menu + Pilha de Títulos Anteriores
    // Adicionamos um pequeno buffer (-2px) para garantir que a borda fique perfeita
    const totalOffset = headerHeight + stackOffset - 2;

    // 4. Executa a rolagem com precisão cirúrgica
    gsap.to(window, {
        duration: 1.5,
        scrollTo: {
            y: targetElement,
            offsetY: totalOffset, // O segredo está aqui: paramos ANTES da pilha cobrir o conteúdo
            autoKill: false
        },
        ease: "power3.inOut"
    });
}

// Mantém compatibilidade com o HTML antigo se necessário
window.scrollToSection = function(id) {
    const el = document.getElementById(id);
    if(el) performStackScroll(el);
};


// =========================================================
//  MÓDULO DE ANIMAÇÕES (GRÁFICOS) - Mantido
// =========================================================
function setupChartAnimations() {
    ScrollTrigger.refresh();
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
                scrollTrigger: {
                    trigger: row,
                    start: "top 90%",
                    toggleActions: "restart none none reverse"
                }
            }
        );

        let proxy = { val: 0 }; 
        gsap.to(proxy, {
            val: numVal,
            duration: 2,
            ease: "power1.out",
            scrollTrigger: {
                trigger: row,
                start: "top 90%",
                toggleActions: "restart none none reverse"
            },
            onUpdate: function() {
                counter.innerText = this.targets()[0].val.toFixed(1).replace('.', ',');
            }
        });
    });
}

// =========================================================
//  MÓDULO INTERATIVO (CARROSSEL E BOTÕES) - Mantido
// =========================================================
window.updateMethodology = function(mode) {
    const container = document.getElementById('bar-display');
    const caption = document.getElementById('caption-dynamic');
    const btnQuintil = document.getElementById('btn-quintil');
    const btnDecil = document.getElementById('btn-decil');

    if (!container) return;

    if (mode === 'quintil') {
        btnQuintil?.classList.add('active');
        btnDecil?.classList.remove('active');
        if(caption) caption.innerText = "2. Dividimos em 5 grupos iguais (Quintis)";
        renderBars(container, 5, 'q');
    } else {
        btnQuintil?.classList.remove('active');
        btnDecil?.classList.add('active');
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
        div.innerHTML = `<span>${percentText}</span>`;
        container.appendChild(div);

        setTimeout(() => {
            div.classList.add('visible');
        }, i * 50);
    }
}

let currentSlide = 0;
window.moveSlide = function(direction) {
    const track = document.getElementById('track');
    const cards = document.querySelectorAll('.platform-card');
    if (!track || cards.length === 0) return;

    const totalSlides = cards.length;
    currentSlide += direction;

    if (currentSlide < 0) currentSlide = totalSlides - 1;
    else if (currentSlide >= totalSlides) currentSlide = 0;

    const transformValue = -(currentSlide * 105);
    track.style.transform = `translateX(${transformValue}%)`;
};