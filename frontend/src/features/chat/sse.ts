import type { ChatStreamEvent } from "@/types/domain";

const FRAME_SEPARATOR = "\n\n";

function parseData(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function createSseParser(): (chunk: string) => ChatStreamEvent[] {
  let buffer = "";

  return (chunk: string): ChatStreamEvent[] => {
    buffer += chunk;
    const frames = buffer.split(FRAME_SEPARATOR);
    buffer = frames.pop() ?? "";

    const events: ChatStreamEvent[] = [];
    for (const frame of frames) {
      let eventName = "";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) {
          eventName = line.slice("event:".length).trim();
        } else if (line.startsWith("data:")) {
          data += line.slice("data:".length).trimStart();
        }
      }
      if (!eventName) continue;
      events.push({ event: eventName, data: parseData(data) } as ChatStreamEvent);
    }
    return events;
  };
}
