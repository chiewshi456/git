import express from "express";
import { createServer } from "node:http";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { WebSocketServer } from "ws";
import type { StreamController } from "../controller/StreamController.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(__dirname, "..", "..");
const projectRoot = resolve(packageRoot, "..");

export function startDashboard(controller: StreamController, port = 3000): void {
  const app = express();
  const server = createServer(app);
  const wss = new WebSocketServer({ server });
  const dashboardPublic = existsSync(resolve(__dirname, "public"))
    ? resolve(__dirname, "public")
    : resolve(packageRoot, "src", "dashboard", "public");

  app.use(express.json());
  app.use((req, res, next) => {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
    if (req.method === "OPTIONS") {
      res.sendStatus(204);
      return;
    }
    next();
  });
  app.use(express.static(dashboardPublic));

  app.get("/game/", (_req, res) => {
    res.sendFile(resolve(projectRoot, "index.html"));
  });

  app.get("/game", (_req, res) => {
    res.redirect("/game/");
  });

  app.get("/game/style.css", (_req, res) => {
    res.sendFile(resolve(projectRoot, "style.css"));
  });

  app.get("/game/game.js", (_req, res) => {
    res.sendFile(resolve(projectRoot, "game.js"));
  });

  app.get("/api/state", (_req, res) => {
    res.json(controller.getSnapshot());
  });

  app.post("/api/messages", (req, res) => {
    const text = typeof req.body?.text === "string" ? req.body.text.trim() : "";
    if (!text) {
      res.status(400).json({ ok: false, error: "text is required" });
      return;
    }

    const message = controller.sendTestMessage(text.slice(0, 500));
    res.status(202).json({ ok: true, message });
  });

  wss.on("connection", (socket) => {
    socket.send(JSON.stringify({ type: "snapshot", payload: controller.getSnapshot() }));

    socket.on("message", (raw) => {
      const message = JSON.parse(raw.toString()) as { action: string; text?: string };
      if (message.action === "start") {
        controller.start();
      }
      if (message.action === "pause") {
        controller.pause();
      }
      if (message.action === "resume") {
        controller.resume();
      }
      if (message.action === "panic") {
        controller.panic();
      }
      if (message.action === "clear_context") {
        controller.clearContext();
      }
      if (message.action === "send_test_message" && message.text) {
        controller.sendTestMessage(message.text);
      }
    });
  });

  controller.setDashboardPush((snapshot) => {
    const payload = JSON.stringify({ type: "snapshot", payload: snapshot });
    for (const client of wss.clients) {
      if (client.readyState === client.OPEN) {
        client.send(payload);
      }
    }
  });

  server.listen(port, () => {
    console.log(`AI VTuber Brain dashboard: http://localhost:${port}`);
    console.log(`Linked city game: http://localhost:${port}/game/`);
  });
}
