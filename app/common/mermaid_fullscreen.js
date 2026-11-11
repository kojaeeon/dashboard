async () => {
    const original = document.getElementById('cDIAGRAM_ID')?.querySelector('svg');
    if (!original) return;
    const opener = document.activeElement;
    const svg = original.cloneNode(true);
    // Inline inherited colors/fonts before moving the copy into its own shadow
    // tree. SVG ids and arrow references cannot collide with the inline chart.
    const originals = [original, ...original.querySelectorAll('*')];
    const copies = [svg, ...svg.querySelectorAll('*')];
    for (let i = 0; i < originals.length; i++) {
        const computed = getComputedStyle(originals[i]);
        for (const property of ['fill', 'stroke', 'stroke-width', 'font-family',
            'font-size', 'font-weight', 'color', 'background-color', 'text-anchor']) {
            copies[i].style.setProperty(property, computed.getPropertyValue(property));
        }
    }
    const box = original.viewBox.baseVal;
    const bounds = original.getBoundingClientRect();
    const width = box.width || bounds.width || 800;
    const height = box.height || bounds.height || 600;
    const dark = document.body.classList.contains('body--dark');
    const dialog = document.createElement('dialog');
    dialog.setAttribute('aria-label', 'Mermaid 전체화면');
    dialog.style.cssText = 'position:fixed;inset:0;margin:0;padding:0;border:0;' +
        'width:100vw;height:100dvh;max-width:none;max-height:none;overflow:hidden;';
    const host = document.createElement('div');
    host.style.cssText = 'width:100%;height:100%;';
    dialog.appendChild(host);
    const shadow = host.attachShadow({mode: 'open'});
    shadow.innerHTML = `<style>
        :host { color-scheme: ${dark ? 'dark' : 'light'}; }
        * { box-sizing: border-box; }
        .shell { height:100%; display:flex; flex-direction:column; font:14px system-ui,sans-serif;
            background:${dark ? '#111412' : '#f4f1eb'}; color:${dark ? '#e9e6df' : '#302c26'}; }
        header { display:flex; align-items:center; flex-wrap:wrap; gap:10px;
            padding:12px 20px; border-bottom:1px solid #b89a6040; flex:none; }
        strong { margin-right:auto; font-size:16px; }
        button { min-width:42px; min-height:42px; padding:8px 12px; border:1px solid #b89a6050;
            border-radius:8px; background:transparent; color:inherit; cursor:pointer; font:inherit; }
        button:hover { background:#b89a6020; }
        button:focus-visible { outline:2px solid #b89a60; outline-offset:2px; }
        button:disabled { opacity:.35; cursor:default; }
        output { min-width:54px; text-align:center; font-variant-numeric:tabular-nums; }
        .viewport { flex:1; min-height:0; overflow:auto; overscroll-behavior:contain;
            cursor:grab; touch-action:none; user-select:none; -webkit-user-select:none; }
        .viewport.is-dragging, .viewport.is-dragging * { cursor:grabbing !important; }
        .canvas { width:max-content; min-width:100%; min-height:100%; padding:24px;
            display:flex; align-items:center; justify-content:center; }
        svg { display:block; flex:none; max-width:none !important; max-height:none !important; }
        footer { padding:8px 20px; font-size:12px; opacity:.7; border-top:1px solid #b89a6025; }
        @media(prefers-reduced-motion:reduce) { * { scroll-behavior:auto; } }
    </style><div class="shell">
        <header><strong>Mermaid</strong>
            <button type="button" data-action="out" aria-label="축소" title="축소">−</button>
            <output aria-label="확대 비율" aria-live="polite">100%</output>
            <button type="button" data-action="in" aria-label="확대" title="확대">＋</button>
            <button type="button" data-action="reset" title="원본 크기">100%</button>
            <button type="button" data-action="fit">화면 맞춤</button>
            <button type="button" data-action="close" aria-label="전체화면 닫기" title="닫기 (Esc)">✕</button>
        </header>
        <div class="viewport" tabindex="0" role="region" aria-label="다이어그램 스크롤 영역"><div class="canvas"></div></div>
        <footer>드래그로 이동 · 휠로 스크롤 · Ctrl+휠로 확대/축소 · Esc 닫기</footer>
    </div>`;
    shadow.querySelector('.canvas').appendChild(svg);
    const viewport = shadow.querySelector('.viewport');
    const output = shadow.querySelector('output');
    let scale = 1, fitted = true, closed = false, nativeFullscreen = false;
    let drag = null, suppressClick = false;
    function endDrag(event) {
        if (!drag || (event?.pointerId !== undefined && event.pointerId !== drag.id)) return;
        const previous = drag;
        drag = null;
        suppressClick = previous.moved;
        viewport.classList.remove('is-dragging');
        if (viewport.hasPointerCapture(previous.id)) viewport.releasePointerCapture(previous.id);
    }
    function resize(next, keepCenter = true) {
        const ratio = Math.max(.1, Math.min(8, next)) / scale;
        const centerX = (viewport.scrollLeft + viewport.clientWidth / 2) * ratio;
        const centerY = (viewport.scrollTop + viewport.clientHeight / 2) * ratio;
        scale = Math.max(.1, Math.min(8, next));
        svg.style.width = `${width * scale}px`;
        svg.style.height = `${height * scale}px`;
        svg.setAttribute('width', width * scale);
        svg.setAttribute('height', height * scale);
        output.textContent = `${Math.round(scale * 100)}%`;
        shadow.querySelector('[data-action="out"]').disabled = scale <= .1;
        shadow.querySelector('[data-action="in"]').disabled = scale >= 8;
        viewport.scrollLeft = keepCenter ? centerX - viewport.clientWidth / 2 : 0;
        viewport.scrollTop = keepCenter ? centerY - viewport.clientHeight / 2 : 0;
    }
    function fit() {
        resize(Math.min((viewport.clientWidth - 48) / width, (viewport.clientHeight - 48) / height, 1), false);
    }
    const observer = new ResizeObserver(() => { if (fitted) fit(); });
    async function close() {
        if (closed) return;
        closed = true;
        endDrag();
        window.removeEventListener('blur', endDrag);
        observer.disconnect();
        document.removeEventListener('fullscreenchange', fullscreenChanged);
        if (document.fullscreenElement === host) await document.exitFullscreen().catch(() => {});
        dialog.close();
        dialog.remove();
        if (opener?.isConnected) opener.focus({preventScroll:true});
    }
    function fullscreenChanged() {
        if (nativeFullscreen && document.fullscreenElement !== host) close();
    }
    shadow.querySelector('header').addEventListener('click', event => {
        const action = event.target.closest('button')?.dataset.action;
        if (!action) return;
        if (action === 'close') { close(); return; }
        fitted = action === 'fit';
        if (fitted) fit();
        else resize(action === 'reset' ? 1 : scale * (action === 'in' ? 1.25 : .8));
    });
    viewport.addEventListener('wheel', event => {
        if (!event.ctrlKey) return;
        event.preventDefault();
        fitted = false;
        resize(scale * (event.deltaY < 0 ? 1.1 : 1 / 1.1));
    }, {passive:false});
    viewport.addEventListener('pointerdown', event => {
        if (!event.isPrimary || event.button !== 0 ||
            event.target.closest('a,button,input,textarea,select')) return;
        suppressClick = false;
        drag = {id:event.pointerId, x:event.clientX, y:event.clientY,
            left:viewport.scrollLeft, top:viewport.scrollTop, moved:false};
        viewport.setPointerCapture(event.pointerId);
    });
    viewport.addEventListener('pointermove', event => {
        if (!drag || event.pointerId !== drag.id) return;
        const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
        if (!drag.moved && Math.hypot(dx, dy) < 4) return;
        drag.moved = true;
        fitted = false;
        viewport.classList.add('is-dragging');
        viewport.scrollLeft = drag.left - dx;
        viewport.scrollTop = drag.top - dy;
        event.preventDefault();
    });
    for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) {
        viewport.addEventListener(name, endDrag);
    }
    viewport.addEventListener('click', event => {
        if (!suppressClick) return;
        event.preventDefault();
        event.stopPropagation();
        suppressClick = false;
    }, true);
    viewport.addEventListener('dragstart', event => event.preventDefault());
    window.addEventListener('blur', endDrag);
    dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
    document.addEventListener('fullscreenchange', fullscreenChanged);
    document.body.appendChild(dialog);
    dialog.showModal();
    observer.observe(viewport);
    fit();
    shadow.querySelector('[data-action="close"]').focus();
    // Native fullscreen when permitted; otherwise the dialog still fills the viewport.
    try {
        await host.requestFullscreen();
        nativeFullscreen = document.fullscreenElement === host;
    } catch (_) {}
}
