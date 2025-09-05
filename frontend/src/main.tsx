import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css"; // activa Tailwind
import App from "./App";

const el = document.getElementById("root");
if (!el) throw new Error("No existe #root en index.html");

createRoot(el).render(
  <StrictMode>
    <App />
  </StrictMode>
);
