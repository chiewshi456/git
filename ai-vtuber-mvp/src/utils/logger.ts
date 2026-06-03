export type LogLevel = "info" | "warn" | "error";

export function log(level: LogLevel, message: string, meta?: unknown): void {
  const line = `[${new Date().toISOString()}] [${level.toUpperCase()}] ${message}`;
  if (meta) {
    console.log(line, meta);
    return;
  }
  console.log(line);
}
