import { api } from "@/lib/http";

export type DownloadParams = Record<string, string | number | boolean | undefined>;

function parseFilename(disposition: string | undefined): string | null {
  if (!disposition) return null;
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
  return match ? decodeURIComponent(match[1]) : null;
}

export async function downloadExport(path: string, params: DownloadParams, fallback: string): Promise<void> {
  const response = await api.get<Blob>(path, { params, responseType: "blob" });
  const filename = parseFilename(response.headers["content-disposition"]) ?? fallback;
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}