import React, { useState } from 'react';
import { convertImage } from './api.js';
import Preview from './components/Preview.jsx';

const defaultParams = {
  denoiseStrength: 1.0,
  edgeSigma: 1.0,
  threshold: 0.2,
};

export default function App() {
  const [file, setFile] = useState(null);
  const [params, setParams] = useState(defaultParams);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setResult(null);
  };

  const updateParam = (key) => (event) => {
    setParams({ ...params, [key]: event.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      setError('Selecciona una imagen para convertir.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const data = await convertImage(file, params);
      setResult(data);
    } catch (err) {
      setError(err.message || 'No se pudo convertir la imagen.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>Image Vectorizer</h1>
        <p>Convierte imágenes rasterizadas a SVG, AI y EPS.</p>
      </header>

      <section className="panel">
        <form onSubmit={handleSubmit}>
          <label className="field">
            Imagen de entrada
            <input type="file" accept="image/*" onChange={handleFileChange} />
          </label>

          <div className="grid">
            <label className="field">
              Reducción de ruido
              <input
                type="number"
                min="0"
                max="5"
                step="0.5"
                value={params.denoiseStrength}
                onChange={updateParam('denoiseStrength')}
              />
            </label>

            <label className="field">
              Sigma de bordes
              <input
                type="number"
                min="0.1"
                max="5"
                step="0.1"
                value={params.edgeSigma}
                onChange={updateParam('edgeSigma')}
              />
            </label>

            <label className="field">
              Umbral
              <input
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={params.threshold}
                onChange={updateParam('threshold')}
              />
            </label>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? 'Procesando…' : 'Convertir'}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      <Preview result={result} />
    </div>
  );
}
