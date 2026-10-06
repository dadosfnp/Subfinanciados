/* ============================================================================
 * fx-secoes.js: navegação entre seções e animação de entrada
 * ----------------------------------------------------------------------------
 * Componente compartilhado das páginas no layout folheto (previews de
 * município, agregado, gráficos e landing). Para usar numa página:
 *
 *   1. marque cada seção com  data-secao="Nome da seção"
 *      (elementos consecutivos com o MESMO nome viram um item só; útil para
 *      capítulo + trilha da landing);
 *   2. opcional: um  <div data-fx-secoes-barra></div>  dentro da barra fixa
 *      da página. Sem ele, o componente cria uma pílula flutuante embaixo;
 *   3. carregue global/css/fx-secoes.css e este arquivo.
 *
 * O que ele monta:
 *   - trilho "anterior · atual · próxima", clicável, com contador (3 de 6);
 *   - pontos na lateral direita (telas largas), um por seção;
 *   - barra fina de progresso da página;
 *   - entrada suave (fade + leve subida) dos blocos de cada seção.
 *
 * Respeita prefers-reduced-motion: sem animação e rolagem instantânea.
 * ========================================================================== */
(function () {
  'use strict';

  var reduzMovimento = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function iniciar() {
    var marcados = Array.prototype.slice.call(document.querySelectorAll('[data-secao]'));
    if (!marcados.length) return;

    // ---- Agrupa elementos consecutivos com o mesmo nome ----
    var secoes = [];
    marcados.forEach(function (el) {
      var nome = el.getAttribute('data-secao');
      var ultima = secoes[secoes.length - 1];
      if (ultima && ultima.nome === nome) ultima.elementos.push(el);
      else secoes.push({ nome: nome, elementos: [el] });
    });

    // Seção escondida (ex.: síntese do agregado sem dado de 2000) sai da navegação.
    function visivel(s) {
      return s.elementos.some(function (el) { return el.offsetParent !== null || el.getClientRects().length > 0; });
    }

    function topoDe(s) {
      return Math.min.apply(null, s.elementos.map(function (el) { return el.getBoundingClientRect().top + window.scrollY; }));
    }

    // Altura da barra fixa da página: a rolagem para a seção desconta, senão o
    // título fica escondido atrás dela.
    function deslocamento() {
      var barra = document.querySelector('.fx-controles');
      return barra ? barra.getBoundingClientRect().height + 8 : 12;
    }

    function irPara(s) {
      if (!s) return;
      window.scrollTo({ top: Math.max(topoDe(s) - deslocamento(), 0), behavior: reduzMovimento ? 'auto' : 'smooth' });
    }

    // ---- Trilho anterior / atual / próxima ----
    var host = document.querySelector('[data-fx-secoes-barra]');
    var flutuante = !host;
    if (flutuante) {
      host = document.createElement('div');
      host.className = 'fx-secoes-flutuante';
      document.body.appendChild(host);
    }
    host.classList.add('fx-secoes-trilho');
    host.setAttribute('role', 'navigation');
    host.setAttribute('aria-label', 'Seções da página');
    host.innerHTML =
      '<button type="button" class="fx-secoes-ant" aria-label="Seção anterior"><span aria-hidden="true">&#8249;</span><em></em></button>' +
      '<span class="fx-secoes-atual"><b></b><small></small></span>' +
      '<button type="button" class="fx-secoes-prox" aria-label="Próxima seção"><em></em><span aria-hidden="true">&#8250;</span></button>' +
      '<span class="fx-secoes-progresso" aria-hidden="true"><i></i></span>';

    var btnAnt = host.querySelector('.fx-secoes-ant');
    var btnProx = host.querySelector('.fx-secoes-prox');
    var elAtualNome = host.querySelector('.fx-secoes-atual b');
    var elAtualConta = host.querySelector('.fx-secoes-atual small');
    var elProgresso = host.querySelector('.fx-secoes-progresso i');

    // ---- Pontos laterais ----
    var pontos = document.createElement('nav');
    pontos.className = 'fx-secoes-pontos';
    pontos.setAttribute('aria-label', 'Ir para a seção');
    secoes.forEach(function (s, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.innerHTML = '<span>' + s.nome.replace(/</g, '&lt;') + '</span>';
      b.setAttribute('aria-label', s.nome);
      b.addEventListener('click', function () { irPara(s); });
      s.ponto = b;
      pontos.appendChild(b);
    });
    document.body.appendChild(pontos);

    // ---- Seção ativa ----
    var indiceAtivo = -1;

    function visiveisAgora() { return secoes.filter(visivel); }

    function atualizar() {
      var lista = visiveisAgora();
      if (!lista.length) return;

      // Ativa = a última cujo topo já passou de 40% da altura da tela.
      var linha = window.scrollY + window.innerHeight * 0.4;
      var ativa = lista[0];
      lista.forEach(function (s) { if (topoDe(s) <= linha) ativa = s; });
      var idx = lista.indexOf(ativa);

      var doc = document.documentElement;
      var total = doc.scrollHeight - window.innerHeight;
      if (elProgresso) elProgresso.style.width = (total > 0 ? Math.min(window.scrollY / total, 1) * 100 : 0) + '%';

      // Pílula flutuante só aparece depois da primeira seção (o hero já se explica).
      if (flutuante) host.classList.toggle('is-visivel', window.scrollY > window.innerHeight * 0.6);

      if (idx === indiceAtivo && host.getAttribute('data-n') === String(lista.length)) return;
      indiceAtivo = idx;
      host.setAttribute('data-n', String(lista.length));

      var ant = lista[idx - 1];
      var prox = lista[idx + 1];
      elAtualNome.textContent = ativa.nome;
      elAtualConta.textContent = (idx + 1) + ' de ' + lista.length;
      btnAnt.querySelector('em').textContent = ant ? ant.nome : '';
      btnProx.querySelector('em').textContent = prox ? prox.nome : '';
      btnAnt.disabled = !ant;
      btnProx.disabled = !prox;
      btnAnt.onclick = function () { irPara(ant); };
      btnProx.onclick = function () { irPara(prox); };

      secoes.forEach(function (s) {
        s.ponto.hidden = !visivel(s);
        var eh = s === ativa;
        s.ponto.classList.toggle('is-ativo', eh);
        if (eh) s.ponto.setAttribute('aria-current', 'true');
        else s.ponto.removeAttribute('aria-current');
      });
    }

    var agendado = false;
    function agendar() {
      if (agendado) return;
      agendado = true;
      window.requestAnimationFrame(function () { agendado = false; atualizar(); });
    }
    window.addEventListener('scroll', agendar, { passive: true });
    window.addEventListener('resize', agendar);
    // Conteúdo que chega depois (APIs do agregado, gráficos) muda as alturas.
    if (window.ResizeObserver) new ResizeObserver(agendar).observe(document.body);
    atualizar();

    // Teclado: Alt + seta para baixo/cima pula de seção sem roubar a rolagem normal.
    document.addEventListener('keydown', function (ev) {
      if (!ev.altKey || (ev.key !== 'ArrowDown' && ev.key !== 'ArrowUp')) return;
      var lista = visiveisAgora();
      var alvo = lista[indiceAtivo + (ev.key === 'ArrowDown' ? 1 : -1)];
      if (!alvo) return;
      ev.preventDefault();
      irPara(alvo);
    });

    // ---- Entrada suave dos blocos ----
    if (reduzMovimento || !('IntersectionObserver' in window)) return;
    var blocos = [];
    secoes.forEach(function (s) {
      s.elementos.forEach(function (el) {
        // Blocos de conteúdo: filhos do container da seção, ou marcados à mão.
        var container = el.querySelector(':scope > .fx-container, :scope > .ap-container') || el;
        Array.prototype.forEach.call(container.children, function (filho) {
          if (filho.matches('script, style, [data-fx-sem-revelar]')) return;
          // Quem tem filhos com animacao propria nao anima inteiro (seria dobrado).
          if (filho.querySelector('[data-fx-revelar]')) return;
          blocos.push(filho);
        });
      });
    });
    document.querySelectorAll('[data-fx-revelar]').forEach(function (el) { blocos.push(el); });

    var observador = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('is-revelado');
        observador.unobserve(e.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    blocos.forEach(function (el, i) {
      // O que já está na tela na carga não anima (evita "piscar" o topo).
      if (el.getBoundingClientRect().top < window.innerHeight * 0.9) return;
      el.classList.add('fx-revelar');
      // Irmãos entram em sequência, com até 3 degraus de atraso.
      el.style.setProperty('--fx-revelar-atraso', (Array.prototype.indexOf.call(el.parentNode.children, el) % 4) * 70 + 'ms');
      observador.observe(el);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
