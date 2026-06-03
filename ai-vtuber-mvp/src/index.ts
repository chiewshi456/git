import { StreamController } from "./controller/StreamController.js";
import { startDashboard } from "./dashboard/server.js";
import { createBrainProvider } from "./brain/createBrainProvider.js";

const controller = new StreamController({ brain: createBrainProvider() });
const port = Number.parseInt(process.env.PORT ?? "3000", 10);
startDashboard(controller, Number.isFinite(port) ? port : 3000);
