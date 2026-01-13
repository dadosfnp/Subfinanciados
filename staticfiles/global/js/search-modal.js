// Command Palette para selects (abre modal, busca com Fuse e aplica no select)
(() => {
  let targetSelect = null;
  let fuse = null;
  let items = [];

  let modalEl = null;
  let listEl  = null;
  let inputEl = null;
  let bsModal = null;

  const $ = (sel, root = document) => root.querySelector(sel);

  // Garante refs e instancia o modal Bootstrap quando existir no DOM
  function ensureRefs() {
    if (modalEl && listEl && inputEl && bsModal) return true;

    modalEl = $('#search-modal');
    listEl  = $('#search-list');
    inputEl = $('#search-input');

    if (!modalEl || !listEl || !inputEl) return false;

    // precisa do bootstrap.bundle já carregado
    bsModal = new bootstrap.Modal(modalEl);
    return true;
  }

  function buildIndexFromSelect(select) {
    items = Array.from(select.options).map(o => ({
      value: o.value,
      label: o.textContent || ''
    }));
    fuse = new Fuse(items, {
      keys: ['label'],
      threshold: 0.35,
      ignoreLocation: true,
      minMatchCharLength: 1
    });
  }

  function renderList(rows) {
    listEl.innerHTML = '';
    rows.forEach(r => {
      const li = document.createElement('button');
      li.type = 'button';
      li.className = 'list-group-item list-group-item-action';
      li.textContent = r.label;
      li.addEventListener('click', () => {
        if (targetSelect) {
          targetSelect.value = r.value;
          targetSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }
        bsModal.hide();
      });
      listEl.appendChild(li);
    });

    if (!rows.length) {
      const empty = document.createElement('div');
      empty.className = 'p-3 text-muted';
      empty.textContent = 'Nada encontrado.';
      listEl.appendChild(empty);
    }
  }

  function openFor(select) {
    if (!ensureRefs()) return;  // Modal ainda não existe no DOM? sai de boa.
    targetSelect = select;
    buildIndexFromSelect(select);
    inputEl.value = '';
    renderList(items);          // lista completa ao abrir
    bsModal.show();
    setTimeout(() => inputEl.focus(), 120);
  }

  // Clique em qualquer botão com data-search-for="#id-do-select"
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-search-for]');
    if (!btn) return;
    const selector = btn.getAttribute('data-search-for');
    const sel = document.querySelector(selector);
    if (sel) openFor(sel);
  });

  // Filtra enquanto digita
  document.addEventListener('input', (e) => {
    if (!inputEl || e.target !== inputEl || !fuse) return;
    const q = inputEl.value.trim();
    if (!q) { renderList(items); return; }
    const out = fuse.search(q).map(x => x.item);
    renderList(out);
  });
})();
