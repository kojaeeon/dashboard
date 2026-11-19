async (sourceId, title) => {
  const waitForRender = async () => {
    const deadline = performance.now() + 8000;
    do {
      const source = document.getElementById(`c${sourceId}`);
      if (source?.childElementCount &&
          [...source.querySelectorAll('.markdown-mermaid')].every(node => node.querySelector('svg'))) {
        return source;
      }
      await new Promise(resolve => setTimeout(resolve, 50));
    } while (performance.now() < deadline);
    return null;
  };

  const source = await waitForRender();
  if (!source) return 'render-timeout';
  if (!source.textContent.trim() && !source.querySelector('img, svg, hr, table')) return 'empty';

  const frame = document.createElement('iframe');
  frame.title = 'PDF 출력';
  frame.setAttribute('sandbox', 'allow-same-origin allow-modals');
  frame.setAttribute('aria-hidden', 'true');
  frame.tabIndex = -1;
  frame.style.cssText = 'position:fixed;left:-10000px;top:0;width:760px;height:1px;border:0';
  frame.srcdoc = '<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body></body></html>';
  const loaded = new Promise(resolve => frame.addEventListener('load', resolve, { once: true }));
  const timeout = new Promise(resolve => setTimeout(() => resolve(false), 8000));
  document.body.append(frame);

  let scheduled = false;
  try {
    if (await Promise.race([loaded.then(() => true), timeout]) === false) return 'render-timeout';
    const printWindow = frame.contentWindow;
    const printDocument = frame.contentDocument;
    printDocument.title = title;
    const style = printDocument.createElement('style');
    style.textContent = `
      @page { size: A4 portrait; margin: 16mm; }
      body {
        margin: 0; color: #232323; background: white; font: 11pt/1.65 system-ui, "Malgun Gothic", sans-serif;
        -webkit-print-color-adjust: exact; print-color-adjust: exact; overflow-wrap: anywhere;
      }
      h1, h2, h3, h4, h5, h6 { break-after: avoid; line-height: 1.3; }
      .nicegui-markdown > :first-child { margin-top: 0; }
      .nicegui-markdown > :last-child { margin-bottom: 0; }
      p, li { orphans: 3; widows: 3; }
      a { color: #174974; }
      .markdown-mermaid { min-height: 0 !important; overflow: visible !important; break-inside: avoid; }
      .markdown-mermaid, #print-document > div + div { margin-top: 12pt; }
      img, svg { max-width: 100%; height: auto; }
      table { width: 100%; border-collapse: collapse; }
      thead { display: table-header-group; }
      tr { break-inside: avoid; }
      th, td { border: 1px solid #d8d6d0; padding: 4pt 6pt; text-align: left; }
      th { background: #f1f0ec; }
      pre { margin: 0; padding: 8pt; background: #f5f5f5; white-space: pre-wrap; tab-size: 4; }
      .nicegui-code { margin: 0; }
      .nicegui-code .nicegui-markdown { overflow: visible !important; height: auto !important; }
      blockquote { margin-inline: 0; padding-inline: 10pt; border-left: 2pt solid #d8d6d0; }
    `;
    printDocument.head.append(style);

    const article = printDocument.importNode(source, true);
    article.id = 'print-document';
    const images = [...article.querySelectorAll('img')];
    images.forEach(image => { image.loading = 'eager'; });
    printDocument.body.append(article);
    const ready = Promise.all([printDocument.fonts.ready, ...images.map(image => image.decode())]);
    if (await Promise.race([ready.then(() => true), timeout]) === false) return 'asset-error';

    printWindow.addEventListener('afterprint', () => setTimeout(() => frame.remove(), 0), { once: true });
    // Let the button handler finish before the native print dialog blocks the page.
    setTimeout(() => { printWindow.focus(); printWindow.print(); }, 0);
    scheduled = true;
    return 'ready';
  } catch {
    return 'asset-error';
  } finally {
    if (!scheduled) frame.remove();
  }
}
