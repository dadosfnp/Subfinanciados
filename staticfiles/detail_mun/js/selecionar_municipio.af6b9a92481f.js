/**
 * Gerenciador de busca e navegação para Análise Detalhada
 * Responsável por consumir a API de municípios e redirecionar para a rota de detalhe.
 */
document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("muni-search-input");
    const autocompleteList = document.getElementById("muni-autocomplete-list");
    let debounceTimer;

    /**
     * Reseta o estado visual do componente de busca
     */
    const clearResults = () => {
        autocompleteList.innerHTML = "";
        autocompleteList.classList.add("hidden");
    };

    /**
     * Listener para fechamento do menu ao perder o foco
     */
    document.addEventListener("click", (event) => {
        if (!searchInput.contains(event.target) && !autocompleteList.contains(event.target)) {
            clearResults();
        }
    });

    searchInput.addEventListener("input", function() {
        const query = this.value.trim();
        clearTimeout(debounceTimer);

        if (query.length < 3) {
            clearResults();
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/api/busca-municipio/?q=${encodeURIComponent(query)}`)
                .then(response => {
                    if (!response.ok) throw new Error("Network response error");
                    return response.json();
                })
                .then(data => {
                    autocompleteList.innerHTML = "";
                    
                    if (data.results && data.results.length > 0) {
                        data.results.forEach(item => {
                            const row = document.createElement("div");
                            row.className = "autocomplete-suggestion";
                            row.textContent = item.nome;
                            
                            // Executa o redirecionamento baseado no ID retornado pela API
                            row.addEventListener("click", () => {
                                window.location.href = `/municipio/${item.id}/`;
                            });
                            
                            autocompleteList.appendChild(row);
                        });
                        autocompleteList.classList.remove("hidden");
                    } else {
                        clearResults();
                    }
                })
                .catch(err => {
                    console.error("Search API Failure:", err);
                    clearResults();
                });
        }, 300); // Latência de 300ms para otimização de requisições (Debounce)
    });
});