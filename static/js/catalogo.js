document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const feedback = document.getElementById('search-feedback');
    const gridRutas = document.getElementById('grid-rutas');
    const noResults = document.getElementById('no-results');
    const formacionPetrolera = document.getElementById('formacion-petrolera');
    const filterLinks = document.querySelectorAll('.filter');

    if (!gridRutas || !searchInput || filterLinks.length === 0) return;

    const cards = gridRutas.querySelectorAll('.card_catalogo');
    let activeFilter = 'todas';
    let searchTerm = searchInput.value || new URLSearchParams(window.location.search).get('q') || '';

    function normalize(str) {
        return str.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
    }

    function updateURL() {
        const params = new URLSearchParams(window.location.search);
        if (searchTerm) params.set('q', searchTerm); else params.delete('q');
        if (activeFilter && activeFilter !== 'todas') params.set('categoria', activeFilter); else params.delete('categoria');
        const qs = params.toString();
        history.replaceState(null, '', qs ? `?${qs}` : window.location.pathname);
    }

    function setActiveFilter(el) {
        filterLinks.forEach(f => {
            f.classList.remove('filter-select');
            f.setAttribute('aria-pressed', 'false');
        });
        el.classList.add('filter-select');
        el.setAttribute('aria-pressed', 'true');
        activeFilter = normalize(el.dataset.filter);
        updateURL();
    }

    function applyFilters() {
        const term = normalize(searchTerm);
        let visibleCount = 0;

        const isPetrolera = activeFilter === 'ruta-petrolera' || activeFilter === 'ruta petrolera';
        const isTodas = activeFilter === 'todas';

        if (isPetrolera) {
            gridRutas.style.display = 'none';
            if (formacionPetrolera) formacionPetrolera.style.display = 'flex';
            if (noResults) noResults.style.display = 'none';
            if (feedback) feedback.textContent = 'Mostrando Ruta Petrolera';
            updateURL();
            return;
        } else {
            gridRutas.style.display = '';
            if (formacionPetrolera) formacionPetrolera.style.display = '';
        }

        cards.forEach(card => {
            const titulo = normalize(card.dataset.titulo || card.querySelector('.titulo_card')?.textContent || '');
            const descripcion = normalize(card.dataset.descripcion || card.querySelector('.parrafo_card')?.textContent || '');
            const categoria = normalize(card.dataset.categoria || '');

            const textoCompleto = `${titulo} ${descripcion} ${categoria}`;
            const matchSearch = term === '' || textoCompleto.includes(term);
            const matchFilter = isTodas || categoria === activeFilter;

            const visible = matchSearch && matchFilter;
            card.style.display = visible ? '' : 'none';
            if (visible) visibleCount++;
        });

        if (noResults) {
            noResults.style.display = visibleCount === 0 ? 'block' : 'none';
        }
        if (feedback) {
            if (term !== '' && visibleCount === 0) {
                feedback.textContent = `Sin resultados para "${searchTerm}"`;
            } else if (term !== '') {
                feedback.textContent = `${visibleCount} resultado(s) para "${searchTerm}"`;
            } else if (!isTodas) {
                feedback.textContent = `${visibleCount} ruta(s) en "${activeFilter}"`;
            } else {
                feedback.textContent = '';
            }
        }
        updateURL();
    }

    filterLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            setActiveFilter(link);
            applyFilters();
        });
    });

    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            searchTerm = searchInput.value;
            applyFilters();
            if (gridRutas.querySelector('.card_catalogo:not([style*="display: none"])')) {
                gridRutas.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
        // debounce typing (progressive, no reemplaza submit)
        let t;
        searchInput.addEventListener('input', () => {
            clearTimeout(t);
            t = setTimeout(() => {
                searchTerm = searchInput.value;
                applyFilters();
            }, 300);
        });
    }

    // Estado inicial desde URL
    const params = new URLSearchParams(window.location.search);
    const urlCat = normalize(params.get('categoria') || '');
    const urlQ = params.get('q') || '';
    if (urlCat) {
        const match = Array.from(filterLinks).find(f => normalize(f.dataset.filter) === urlCat);
        if (match) setActiveFilter(match);
    }
    if (urlQ) {
        searchTerm = urlQ;
        searchInput.value = urlQ;
    }
    const initialActive = document.querySelector('.filter-select');
    if (initialActive) activeFilter = normalize(initialActive.dataset.filter);
    applyFilters();
});
