gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

document.addEventListener("DOMContentLoaded", () => {

    
    /* 0. Botão do Hero */
    const heroScrollBtn = document.querySelector('.scroll-indicator');
    if (heroScrollBtn) {
        heroScrollBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollToId('problema'); 
        });
    }
    
    /* 1. Controle de Visibilidade da Barra de Navegação */
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

    /* 2. Highlight dos Itens do Menu e Progresso de Leitura */
    const sectionMap = [
        { id: 'problema', navId: 'nav-problema' },
        { id: 'evolucao', navId: 'nav-evolucao' },
        { id: 'metodologia', navId: 'nav-intro' },
        { id: 'funcionalidades', navId: 'nav-plataforma' },
        { id: 'faq', navId: 'nav-faq' },
        { id: 'noticias', navId: 'nav-noticias' }
    ];
    
    sectionMap.forEach((item, index) => {
        const section = document.getElementById(item.id);
        const navItem = document.getElementById(item.navId);
        
        if (section && navItem) {
            ScrollTrigger.create({
                trigger: section,
                start: "top 60%", 
                end: "bottom 60%",
                onToggle: (self) => {
                    if (self.isActive) {
                        document.querySelectorAll('.story-item').forEach(el => el.classList.remove('active'));
                        navItem.classList.add('active');
                        const progress = ((index + 1) / sectionMap.length) * 100;
                        gsap.to('#reading-progress', { width: `${progress}%`, duration: 0.3 });
                    }
                }
            });

            navItem.addEventListener('click', (e) => {
                e.preventDefault();
                window.scrollToId(item.id);
            });
        }
    });

    /* 3. Destaque Cruzado Multi-Alvo (Scrollytelling: Texto -> Gráficos) */
    document.querySelectorAll('.text-highlight').forEach(trigger => {
        const targets = trigger.getAttribute('data-target').split(',');

        trigger.addEventListener('mouseenter', () => {
            targets.forEach(id => {
                const el = document.getElementById(id.trim());
                if (!el) return;

                const bar = el.classList.contains('stacked-segment') ? el : el.querySelector('.chart-bar');
                
                if (bar) {
                    const barColor = window.getComputedStyle(bar).backgroundColor;
                    el.style.setProperty('--bar-color', barColor);
                }
                
                el.classList.add('highlight-active');
            });
        });

        trigger.addEventListener('mouseleave', () => {
            targets.forEach(id => {
                const el = document.getElementById(id.trim());
                if (el) {
                    el.classList.remove('highlight-active');
                    el.style.removeProperty('--bar-color');
                }
            });
        });
    });

    /* 4. Animação dos Gráficos de Barra (Seção: Problema) */
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
                duration: 2.5, 
                ease: "power2.out",
                scrollTrigger: { 
                    trigger: row, 
                    start: "top 90%",
                    toggleActions: "play none none reverse",
                    fastScrollEnd: true
                }
            }
        );

        let proxy = { val: 0 };
        gsap.to(proxy, {
            val: numVal,
            duration: 3, 
            scrollTrigger: { 
                trigger: row, 
                start: "top 90%",
                toggleActions: "play none none reverse",
                fastScrollEnd: true
            },
            onUpdate: function() {
                counter.innerText = this.targets()[0].val.toFixed(1).replace('.', ',');
            }
        });
    });

    /* 5. Gráfico de Pizza SVG (Receitas) */
    const pieContainer = document.querySelector('.pie-chart-container');
    if (pieContainer) {
        const tlPie = gsap.timeline({
            scrollTrigger: {
                trigger: pieContainer,
                start: "top 85%", 
                toggleActions: "play none none reverse",
                fastScrollEnd: true
            }
        });

        const progressCircle = pieContainer.querySelector('.circle-progress');
        const targetOffset = progressCircle.getAttribute('data-offset');
        
        tlPie.to(progressCircle, { 
            strokeDashoffset: targetOffset,
            duration: 3, 
            ease: "power4.out" 
        }, 0);

        pieContainer.querySelectorAll('.pie-counter').forEach(counter => {
            const targetVal = parseInt(counter.getAttribute('data-target'));
            let proxy = { val: 0 };
            tlPie.to(proxy, {
                val: targetVal,
                duration: 3, 
                ease: "power4.out",
                onUpdate: function() {
                    counter.innerText = Math.floor(this.targets()[0].val);
                }
            }, 0);
        });

        tlPie.from(pieContainer, {
            y: 30,
            opacity: 0,
            duration: 0.8,
            ease: "power2.out"
        }, 0);
    }

    /* 6. Gráficos de População (Barras Laterais) */
    const popGroups = document.querySelectorAll('.pop-chart-group');
    popGroups.forEach(group => {
        gsap.to(group.querySelectorAll('.pop-bar'), {
            width: function(i, target) { return target.getAttribute('data-width'); },
            duration: 2.5, 
            ease: "power2.out",
            stagger: 0.2, 
            scrollTrigger: {
                trigger: group,
                start: "top 90%",
                toggleActions: "play none none reverse",
                fastScrollEnd: true
            }
        });
    });

    /* 7. Gráficos Seção Evolução (Barras e Stacked) */
    const evolutionCharts = document.querySelectorAll('.chart-data-container');
    evolutionCharts.forEach(container => {
        const bars = container.querySelectorAll('.chart-bar');
        bars.forEach(bar => {
            const targetWidth = bar.style.getPropertyValue('--bar-width').trim();
            gsap.fromTo(bar, 
                { width: "0%" }, 
                { 
                    width: targetWidth, 
                    duration: 2.5, 
                    ease: "power2.out",
                    scrollTrigger: {
                        trigger: container,
                        start: "top 90%",
                        toggleActions: "play none none reverse",
                        fastScrollEnd: true
                    }
                }
            );
        });
    });

    const stackedCharts = document.querySelectorAll('.stacked-chart-container');
    stackedCharts.forEach(container => {
        const segments = container.querySelectorAll('.stacked-segment');
        segments.forEach(segment => {
            const targetWidth = segment.style.getPropertyValue('--segment-width').trim();
            gsap.fromTo(segment, 
                { width: "0%" }, 
                { 
                    width: targetWidth, 
                    duration: 2.5, 
                    ease: "power2.out",
                    scrollTrigger: {
                        trigger: container,
                        start: "top 90%",
                        toggleActions: "play none none reverse",
                        fastScrollEnd: true
                    }
                }
            );
        });
    });

/* 8. Animação Sequencial da Metodologia (Barras) */
    const secMetodologia = document.querySelector('#metodologia');
    
    if (secMetodologia) {
        const tlMetodo = gsap.timeline({
            scrollTrigger: {
                trigger: secMetodologia,
                start: 'top 75%',
                toggleActions: 'play none none reverse'
            }
        });

        tlMetodo.from('.bars-container .bar', {
            height: 0,
            opacity: 0,
            stagger: 0.05,
            duration: 0.4,
            ease: 'power2.out'
        });
    }

    /* 9. Lógica do Elemento Expansível (Botão Saiba Mais) */
    const expandButtons = document.querySelectorAll('.btn-read-more');

    expandButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault(); 
            
            const content = this.nextElementSibling;
            const spanText = this.querySelector('.btn-text');
            
            if (!content) return;

            const isExpanded = this.classList.contains('active');

            if (isExpanded) {
                this.classList.remove('active');
                this.setAttribute('aria-expanded', 'false');
                content.style.maxHeight = null;
                if (spanText) spanText.textContent = "Saiba mais";
            } else {
                this.classList.add('active');
                this.setAttribute('aria-expanded', 'true');
                content.style.maxHeight = content.scrollHeight + "px";
                if (spanText) spanText.textContent = "Mostrar menos";
            }

            /* Força atualização do ScrollTrigger após a transição de altura do DOM */
            setTimeout(() => {
                ScrollTrigger.refresh();
            }, 500); 
        });
    });

    /* 10. Navegação Horizontal de Notícias */
    const newsContainer = document.getElementById('news-scroll-container');
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');

    if (newsContainer && prevBtn && nextBtn) {
        
        const scrollAmount = 344; 
        
        nextBtn.addEventListener('click', () => {
            newsContainer.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });

        prevBtn.addEventListener('click', () => {
            newsContainer.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });

        const updateArrows = () => {
            const scrollLeft = newsContainer.scrollLeft;
            const scrollWidth = newsContainer.scrollWidth;
            const clientWidth = newsContainer.clientWidth;
            const maxScroll = scrollWidth - clientWidth;

            if (scrollLeft > 10) {
                prevBtn.classList.add('visible');
            } else {
                prevBtn.classList.remove('visible');
            }

            if (scrollLeft < maxScroll - 10) {
                nextBtn.classList.add('visible');
            } else {
                nextBtn.classList.remove('visible');
            }
        };

        newsContainer.addEventListener('scroll', updateArrows);
        window.addEventListener('resize', updateArrows);
        
        setTimeout(updateArrows, 100);
    }

    /* 11. Tooltips de Informação */
    document.querySelectorAll('.info-tooltip').forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const content = this.querySelector('.tooltip-content');
            if (!content) return;
            this.classList.remove('tooltip-down');
            const rect = this.getBoundingClientRect();
            const requiredSpaceTop = 200; 
            if (rect.top < requiredSpaceTop) {
                this.classList.add('tooltip-down');
            }
        });
        tooltip.addEventListener('mouseleave', function() {
            this.classList.remove('tooltip-down');
        });
    });
});

/* ======================================================================
   12. Funções Globais (Escopo externo ao DOMContentLoaded)
   ====================================================================== */

/* Gerenciamento de Scroll Suave com compensação de Header fixo */
window.scrollToId = function(id) {
    const navHeight = 80; 
    const target = document.getElementById(id);
    if (!target) return;

    gsap.killTweensOf(window);
    ScrollTrigger.refresh();

    gsap.to(window, {
        duration: 1.2, 
        scrollTo: { y: target, offsetY: navHeight },
        ease: "power4.out",
        overwrite: "auto",
        onComplete: () => {
            ScrollTrigger.refresh();
        }
    });
};

/* Controle de Carrossel In-place: Seção O Problema */
window.slideProblema = function(index) {
    const track = document.getElementById('problema-slider');
    if (track) {
        // 1. Faz o painel deslizar para o lado
        const percentage = index * -50;
        track.style.transform = `translateX(${percentage}%)`;

        // 2. Trava o texto no começo e sobe a tela
        setTimeout(() => {
            const panels = track.querySelectorAll('.slider-panel-prob');
            
            if (panels[index]) {
                // Acha a caixa que tem o texto longo com scroll
                const textBox = panels[index].querySelector('.scrollable-text');
                
                // Força o scroll interno do texto a voltar para o 0 (topo)
                if (textBox) {
                    textBox.scrollTop = 0; 
                }

                // No mobile, dá um "puxão" na tela principal para o topo do painel
                if (window.innerWidth < 992) {
                    const viewport = track.parentElement; 
                    if (viewport) {
                        // Calcula o topo exato dando o desconto de 90px do menu azul
                        const topPos = viewport.getBoundingClientRect().top + window.scrollY - 90;
                        
                        gsap.to(window, {
                            duration: 0.5,
                            scrollTo: topPos,
                            ease: "power2.out",
                            overwrite: "auto"
                        });
                    }
                }
            }
        }, 50); 
    }
};

/* Navegação do Carrossel de Plataforma */
window.moveSlide = function(direction) {
    let currentSlide = 0;
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

/* Lógica de acionamento do Modal de Vídeo Tutorial */
window.toggleTutorial = function() {
    const modal = document.getElementById('tutorialModal');
    
    if (!modal) return;

    const isActive = modal.classList.toggle('active');
    
    if (isActive) {
        document.body.style.overflow = 'hidden';
    } else {
        document.body.style.overflow = '';
    }
};

/* Widget_busca_municipio.js gerencia a busca assíncrona e exibição de indicadores municipais */
document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("muni-search-input");
    const autocompleteList = document.getElementById("muni-autocomplete-list");
    let debounceTimer;

    if (!searchInput) return;

    // 1. Gerenciador de Input com Debounce
    searchInput.addEventListener("input", function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();

        if (query.length < 3) {
            autocompleteList.innerHTML = "";
            autocompleteList.classList.add("hidden");
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/api/busca-municipio/?q=${encodeURIComponent(query)}`)
                .then(response => {
                    if (!response.ok) throw new Error('Erro na requisição');
                    return response.json();
                })
                .then(data => {
                    renderAutocomplete(data.results, data.national_avg);
                })
                .catch(err => console.error("Busca falhou:", err));
        }, 300);
    });

    // 2. Renderizador da lista de sugestões (Dropdown)
    function renderAutocomplete(results, nationalAvg) {
        autocompleteList.innerHTML = "";
        
        if (!results || results.length === 0) {
            autocompleteList.innerHTML = `<div style="padding:12px; color:#94a3b8;">Nenhum município encontrado.</div>`;
        } else {
            results.forEach(muni => {
                const item = document.createElement("div");
                item.className = "autocomplete-suggestion";
                item.innerHTML = `<strong>${muni.nome}</strong>`;
                item.addEventListener("click", () => {
                    searchInput.value = muni.nome;
                    autocompleteList.classList.add("hidden");
                    renderResultCard(muni, nationalAvg);
                });
                autocompleteList.appendChild(item);
            });
        }
        autocompleteList.classList.remove("hidden");
    }

    /**
     * Atualiza o DOM com os dados do município selecionado, aplicando
     * formatação de moeda, cálculo de variação e colorização de badges
     * baseada na distribuição em quintis/decis.
     * * @param {Object} muni - Dados do município retornados pela API.
     * @param {number} nationalAvg - Média nacional de receita per capita.
     */
    function renderResultCard(muni, nationalAvg) {
        const container = document.getElementById("muni-result-container");
        if (!container) return;

        const formatBRL = (v) => new Intl.NumberFormat('pt-BR', { 
            style: 'currency', currency: 'BRL' 
        }).format(v || 0);

        const diffPercent = ((muni.rc_pc - nationalAvg) / nationalAvg) * 100;
        const isAbove = muni.rc_pc >= nationalAvg;

        document.getElementById("res-muni-nome").innerText = muni.nome;
        document.getElementById("res-muni-pc").innerText = formatBRL(muni.rc_pc);

        const percentWrapper = document.getElementById("res-muni-percent-wrapper");
        const percentBadge = document.getElementById("res-muni-percent-badge");
        
        if (percentBadge && percentWrapper) {
            const arrow = isAbove ? '▲' : '▼';
            const signalClass = isAbove ? 'badge-positive' : 'badge-negative';
            
            percentBadge.innerText = `${arrow} ${Math.abs(diffPercent).toFixed(1)}%`;
            percentBadge.className = `muni-percent-tag ${signalClass}`;
            
            const tooltipDetalhe = isAbove 
                ? 'Indica que o município tem receita per capita maior que a média nacional.' 
                : 'Indica que o município tem receita per capita menor que a média nacional.';
                
            percentWrapper.setAttribute('data-tooltip', tooltipDetalhe);
        }

        /* Mapeamento de paletas institucionais */
        const quintilColors = {
            1: { bg: '#A81C21', text: '#ffffff' },
            2: { bg: '#E47326', text: '#ffffff' },
            3: { bg: '#F4D01D', text: '#1e293b' },
            4: { bg: '#6AC074', text: '#1e293b' },
            5: { bg: '#1C9148', text: '#ffffff' }
        };

        const decilColors = {
            1: { bg: '#960E16', text: '#ffffff' },
            2: { bg: '#CF3026', text: '#ffffff' },
            3: { bg: '#EB6630', text: '#ffffff' },
            4: { bg: '#F8A555', text: '#ffffff' },
            5: { bg: '#FCE182', text: '#1e293b' },
            6: { bg: '#DDEC88', text: '#1e293b' },
            7: { bg: '#9DD57D', text: '#1e293b' },
            8: { bg: '#60BA69', text: '#1e293b' },
            9: { bg: '#2D964D', text: '#ffffff' },
            10: { bg: '#076931', text: '#ffffff' }
        };

        const quintilNum = parseInt(muni.quintil) || 0;
        const badgeQuintil = document.getElementById("badge-quintil");
        
        if (quintilNum > 0) {
            badgeQuintil.innerText = `${quintilNum}º Quintil`;
            badgeQuintil.style.backgroundColor = quintilColors[quintilNum].bg;
            badgeQuintil.style.color = quintilColors[quintilNum].text;
            badgeQuintil.style.border = "none";
        } else {
            badgeQuintil.innerText = "-";
            badgeQuintil.style.backgroundColor = "#f1f5f9";
            badgeQuintil.style.color = "#475569";
        }

        const decilNum = parseInt(muni.decil) || 0;
        const badgeDecil = document.getElementById("badge-decil");
        
        if (decilNum > 0) {
            badgeDecil.innerText = `${decilNum}º Decil`;
            badgeDecil.style.backgroundColor = decilColors[decilNum].bg;
            badgeDecil.style.color = decilColors[decilNum].text;
            badgeDecil.style.border = "none";
        } else {
            badgeDecil.innerText = "-";
            badgeDecil.style.backgroundColor = "#f1f5f9";
            badgeDecil.style.color = "#475569";
        }

        container.classList.remove("hidden");
    }

    // Fechar ao clicar fora
    document.addEventListener("click", (e) => {
        if (e.target !== searchInput) autocompleteList.classList.add("hidden");
    });
});

/* Lógica do Accordion da FAQ */
document.addEventListener('DOMContentLoaded', () => {
    const accordionItems = document.querySelectorAll('.accordion-item');

    accordionItems.forEach(item => {
        const header = item.querySelector('.accordion-header');
        
        header.addEventListener('click', () => {
            // Verifica se o item atual já está ativo
            const isActive = item.classList.contains('active');
            
            // Fecha todos os itens
            accordionItems.forEach(otherItem => {
                otherItem.classList.remove('active');
                otherItem.querySelector('.accordion-header').setAttribute('aria-expanded', 'false');
            });
            
            // Se o item clicado NÃO estava ativo, abre ele
            if (!isActive) {
                item.classList.add('active');
                header.setAttribute('aria-expanded', 'true');
            }
        });
    });
});

