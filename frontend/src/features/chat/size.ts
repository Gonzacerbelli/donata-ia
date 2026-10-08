export const SIZE_KEY = "donata.chat.size";

export const MIN_WIDTH = 320;
export const MIN_HEIGHT = 400;

export const DEFAULT_SIZE = { width: 400, height: 600 };

export interface WidgetSize {
  width: number;
  height: number;
}

export function clampSize(size: WidgetSize, viewport: WidgetSize): WidgetSize {
  const maxWidth = Math.max(MIN_WIDTH, viewport.width - 32);
  const maxHeight = Math.max(MIN_HEIGHT, viewport.height - 32);
  return {
    width: Math.min(Math.max(size.width, MIN_WIDTH), maxWidth),
    height: Math.min(Math.max(size.height, MIN_HEIGHT), maxHeight),
  };
}

export function parseSize(raw: string | null, viewport: WidgetSize): WidgetSize {
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as Partial<WidgetSize>;
      if (typeof parsed.width === "number" && typeof parsed.height === "number") {
        return clampSize({ width: parsed.width, height: parsed.height }, viewport);
      }
    } catch {
      return clampSize(DEFAULT_SIZE, viewport);
    }
  }
  return clampSize(DEFAULT_SIZE, viewport);
}
