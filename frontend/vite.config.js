import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, ".", "");
    return {
        base: env.VITE_BASE_PATH || "/",
        plugins: [react()],
        server: {
            port: 5173,
            host: "0.0.0.0"
        }
    };
});
