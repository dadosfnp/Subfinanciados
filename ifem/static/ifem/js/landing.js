/* ifem/static/ifem/js/landing.js */

document.addEventListener("DOMContentLoaded", function() {
    gsap.registerPlugin(ScrollTrigger);
    console.log("IFEM: Animações iniciadas.");

    // 1. ANIMAÇÃO DO HERO (Enquanto a cortina sobe)
    // O texto sobe um pouco e desaparece para dar profundidade
    gsap.to(".hero-content", {
        scrollTrigger: {
            trigger: "body",      // Gatilho é o corpo todo
            start: "top top",     // Início da rolagem
            end: "100vh top",     // Até o hero sumir
            scrub: true           // Animação atrelada ao scroll
        },
        y: -150, // Move para cima
        opacity: 0 // Desaparece
    });

    // 2. ENTRADA DOS ELEMENTOS (Fade In Up)
    gsap.utils.toArray(".fade-in-up").forEach(elem => {
        gsap.from(elem, {
            scrollTrigger: {
                trigger: elem,
                start: "top 85%",
                toggleActions: "play none none reverse"
            },
            y: 50,
            opacity: 0,
            duration: 1,
            ease: "power3.out"
        });
    });

    // 3. CONTADORES NUMÉRICOS (CORRIGIDO)
    const counters = [
        { id: "counter1", endVal: 38, suffix: " mi", decimal: false },
        { id: "counter2", endVal: 74.5, suffix: " mi", decimal: true }
    ];

    counters.forEach(c => {
        const el = document.getElementById(c.id);
        if (el) {
            let proxy = { val: 0 };
            gsap.to(proxy, {
                val: c.endVal,  // <--- CORRIGIDO: Agora usa a variável certa!
                duration: 2.5,
                ease: "power2.out",
                scrollTrigger: {
                    trigger: "#" + c.id,
                    start: "top 90%",
                    once: true
                },
                onUpdate: function() {
                    let current = proxy.val;
                    if (c.decimal) {
                        el.innerText = current.toFixed(1).replace('.', ',') + c.suffix;
                    } else {
                        el.innerText = Math.ceil(current) + c.suffix;
                    }
                }
            });
        }
    });

    // 4. GRÁFICO PIZZA
    if(document.querySelector(".pie-slice")){
        gsap.from(".pie-slice", {
            scrollTrigger: { trigger: ".ratio", start: "top 80%" },
            scale: 0, 
            duration: 0.8, 
            stagger: 0.2, 
            ease: "back.out(1.7)"
        });
    }
});