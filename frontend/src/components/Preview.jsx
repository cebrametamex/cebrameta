import React from 'react';

function downloadFile(content, mimeType, filename, isBase64 = false) {
  const blob = isBase64
    ? new Blob([Uint8Array.from(atob(content), (c) => c.charCodeAt(0))], { type: mimeType })
    : new Blob([content], { type: mimeType });

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export default function Preview({ result }) {
  if (!result) {
    return (
      <section className="preview empty">
        <p>Sube una imagen y ejecuta la conversión para ver el resultado.</p>
      </section>
    );
  }

  const handleDownload = (format) => () => {
    if (format === 'svg') {
      downloadFile(result.svg, 'image/svg+xml', 'vectorized.svg');
    } else if (format === 'ai') {
      downloadFile(result.ai, 'application/postscript', 'vectorized.ai', true);
    } else if (format === 'eps') {
      downloadFile(result.eps, 'application/postscript', 'vectorized.eps', true);
    }
  };

  return (
    <section className="preview">
      <h2>Vista previa</h2>
      <div className="preview-content">
        <div className="preview-svg" dangerouslySetInnerHTML={{ __html: result.svg }} />
        <div className="download-buttons">
          <button type="button" onClick={handleDownload('svg')}>
            Descargar SVG
          </button>
          <button type="button" onClick={handleDownload('ai')}>
            Descargar AI
          </button>
          <button type="button" onClick={handleDownload('eps')}>
            Descargar EPS
          </button>
        </div>
      </div>
    </section>
  );
}
