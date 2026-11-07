// Extend the bundled CodeMirror search without changing its matching rules.
(async () => {
    const CM = await import('nicegui-codemirror');
    const component = getElement(EDITOR_ID);
    const view = component?.editor;
    if (!view) return;
    if (view.dom.dataset.searchOverview) return;
    view.dom.dataset.searchOverview = 'true';
    const ruler = document.createElement('div');
    ruler.className = 'search-overview';
    ruler.setAttribute('aria-label', '문서 전체 검색 위치');
    view.dom.appendChild(ruler);
    let matches = [], previousDoc, previousQuery;
    let scheduled = false;
    function draw() {
        scheduled = false;
        if (!view.dom.isConnected) return;
        const panel = view.dom.querySelector('.cm-search');
        ruler.hidden = !panel;
        if (!panel) return;
        // The bundled search field exposes the exact query cursor, including
        // case, whole-word and regex behavior, through its state value.
        const search = view.state.values.find(value =>
            value?.query?.spec && typeof value.query.spec.getCursor === 'function');
        const query = search?.query.spec;
        let counter = panel.querySelector('.search-match-count');
        if (!counter) {
            counter = document.createElement('span');
            counter.className = 'search-match-count';
            counter.setAttribute('role', 'status');
            counter.setAttribute('aria-live', 'polite');
            panel.querySelector('input[name="search"]').after(counter);
        }
        if (previousDoc !== view.state.doc || previousQuery !== query) {
            matches = [];
            if (query?.valid && query.search) {
                const cursor = query.getCursor(view.state);
                while (!cursor.next().done) matches.push({...cursor.value});
            }
            previousDoc = view.state.doc;
            previousQuery = query;
        }
        const selection = view.state.selection.main;
        const current = matches.findIndex(m => m.from === selection.from && m.to === selection.to);
        counter.textContent = query && !query.valid ? '잘못된 검색식' :
            `${current < 0 ? 0 : current + 1} / ${matches.length}`;
        ruler.replaceChildren();
        const lines = view.state.doc.lines;
        // Group results on the same line to keep large searches responsive.
        const markers = new Map();
        matches.forEach((match, index) => {
            const line = view.state.doc.lineAt(match.from).number;
            if (!markers.has(line) || index === current) markers.set(line, {match, index});
        });
        for (const [line, {match, index}] of markers) {
            const marker = document.createElement('button');
            marker.className = 'search-location' + (index === current ? ' is-current' : '');
            marker.style.top = `${(line - 1) / Math.max(1, lines - 1) * 98}%`;
            marker.title = `${index + 1} / ${matches.length} · ${line}행`;
            marker.setAttribute('aria-label', marker.title);
            marker.onclick = () => {
                view.dispatch({selection: {anchor: match.from, head: match.to},
                    effects: CM.EditorView.scrollIntoView(match.from, {y: 'center'})});
                view.focus();
            };
            ruler.appendChild(marker);
        }
    }
    function schedule() {
        if (!scheduled) { scheduled = true; requestAnimationFrame(draw); }
    }
    view.dispatch({effects: CM.StateEffect.appendConfig.of(CM.EditorView.updateListener.of(schedule))});
    schedule();
})();
