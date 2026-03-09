/* map-ui.js - Gerenciamento de eventos de UI do Mapa (Offcanvas, Modal de Busca e Filtros) */
document.addEventListener('DOMContentLoaded', function() {
  const searchModal = document.getElementById('search-modal');
  const filtrosOffcanvas = document.getElementById('filtrosOffcanvas');
  const filtersContainer = document.getElementById('filters');
  const btnLimpar = document.getElementById('btn-limpar-filtros');
  
  if (!filtrosOffcanvas) return;
  const offcanvasInstance = bootstrap.Offcanvas.getOrCreateInstance(filtrosOffcanvas);

  /* Recolhe o painel de filtros em dispositivos mobile apos selecao */
  if (filtersContainer) {
    const allSelects = filtersContainer.querySelectorAll('select');
    allSelects.forEach(select => {
      select.addEventListener('change', function() {
        if (window.innerWidth < 992) {
          setTimeout(() => {
            offcanvasInstance.hide();
          }, 400); 
        }
      });
    });
  }

  /* Recolhe o painel de filtros em dispositivos mobile ao limpar a selecao */
  if (btnLimpar) {
    btnLimpar.addEventListener('click', function() {
      if (window.innerWidth < 992) {
        setTimeout(() => {
          offcanvasInstance.hide();
        }, 300);
      }
    });
  }

  /* Gerencia a sobreposicao do modal de busca em relacao ao offcanvas */
  if (searchModal) {
    searchModal.addEventListener('show.bs.modal', function () {
      offcanvasInstance.hide();
    });

    searchModal.addEventListener('hidden.bs.modal', function () {
      if (window.innerWidth < 992) {
        offcanvasInstance.show();
      }
    });
  }
});