// main.jsx 只做一件事：把 <App /> 这个组件塞进 HTML 里的
// <div id="root">。之后所有页面内容全部由 App.jsx 决定。

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
