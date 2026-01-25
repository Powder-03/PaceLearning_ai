import { API_BASE_URL, getAuthHeaders } from './api';

export const pdfService = {
  // Download DPP (Daily Practice Problems) PDF
  downloadDPP: async (sessionId: string, day: number): Promise<void> => {
    const url = `${API_BASE_URL}/pdf/${sessionId}/dpp/${day}`;
    const headers = getAuthHeaders();

    try {
      const response = await fetch(url, { headers });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to generate DPP' }));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Failed to generate DPP');
      }

      // Get the blob and create download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      
      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `DPP_Day${day}.pdf`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/);
        if (match) filename = match[1];
      }

      // Trigger download
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      throw error;
    }
  },

  // Download Notes PDF
  downloadNotes: async (sessionId: string, day: number): Promise<void> => {
    const url = `${API_BASE_URL}/pdf/${sessionId}/notes/${day}`;
    const headers = getAuthHeaders();

    try {
      const response = await fetch(url, { headers });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to generate notes' }));
        throw new Error(typeof error.detail === 'string' ? error.detail : 'Failed to generate notes');
      }

      // Get the blob and create download
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      
      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `Notes_Day${day}.pdf`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/);
        if (match) filename = match[1];
      }

      // Trigger download
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      throw error;
    }
  },
};
