import { io } from "socket.io-client";
import { api } from "./api";

let socket = null;

export function getSocket() {
  if (!socket) {
    const token = localStorage.getItem("sthira_token");
    socket = io(api.baseUrl, {
      autoConnect: false,
      transports: ["websocket"],
      auth: token ? { token } : {},
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });
  }
  return socket;
}

export function connectSocket() {
  // Refresh auth token each time we connect
  const token = localStorage.getItem("sthira_token");
  const s = getSocket();
  s.auth = token ? { token } : {};
  if (!s.connected) s.connect();
  return s;
}

export function disconnectSocket() {
  if (socket && socket.connected) socket.disconnect();
}
