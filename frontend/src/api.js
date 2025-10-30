const API_URL = import.meta.env.VITE_API_URL || '/convert';

export async function convertImage(file, params) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('denoise_strength', params.denoiseStrength);
  formData.append('edge_sigma', params.edgeSigma);
  formData.append('threshold', params.threshold);

  const response = await fetch(API_URL, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Error en el backend');
  }

  return response.json();
}
