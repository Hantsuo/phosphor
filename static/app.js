// PHOSPHOR BBS - terminal client.

class PhosphorClient {
    constructor() {
        this.screen = document.getElementById("screen");
        this.statusEl = document.getElementById("status");
        this.onlineEl = document.getElementById("online");
        this.term = new PhosphorTerm(this.screen, { cols: 80, rows: 24 });
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.fastMode = new URLSearchParams(window.location.search).get("fast") === "1";
        this.bindKeys();
        this.connect();
        setInterval(() => this.healthCheck(), 15000);
        this.term.focus();
    }

    bindKeys() {
        this.screen.addEventListener("click", () => this.term.focus());
        document.addEventListener("keydown", (event) => {
            if (event.key === "F12") {
                event.preventDefault();
                this.toggleFastMode();
                return;
            }
            if (event.ctrlKey && (event.key === "c" || event.key === "C")) {
                event.preventDefault();
                this.sendKey("\x03");
                return;
            }
            if (event.ctrlKey || event.metaKey || event.altKey) return;

            let key = null;
            if (event.key === "Enter") key = "\r";
            else if (event.key === "Backspace") key = "\x7f";
            else if (event.key === "Escape") key = "\x1b";
            else if (event.key.length === 1) key = event.key;

            if (key !== null) {
                event.preventDefault();
                this.sendKey(key);
            }
        });
    }

    connect() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        let url = `${protocol}//${window.location.host}/ws`;
        const params = new URLSearchParams();
        if (this.fastMode) params.set("fast", "1");
        if (new URLSearchParams(window.location.search).get("guest") === "1") params.set("guest", "1");
        const deepBoard = new URLSearchParams(window.location.search).get("board");
        if (deepBoard) params.set("board", deepBoard);
        const deepScreen = new URLSearchParams(window.location.search).get("screen");
        if (deepScreen) params.set("screen", deepScreen);
        if ([...params].length) url += `?${params.toString()}`;

        this.status("CONNECTING");
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
            this.status("CARRIER UP");
            this.healthCheck();
            this.term.focus();
        };

        this.ws.onmessage = (event) => {
            let msg;
            try { msg = JSON.parse(event.data); } catch (err) { return; }
            if (msg.t === "frame") {
                if (msg.d === "carrier lost") {
                    this.term.write("\r\n\r\n*** CARRIER LOST ***\r\n");
                    this.status("NO CARRIER");
                    this.ws.close();
                    return;
                }
                this.term.write(msg.d);
            }
        };

        this.ws.onclose = () => {
            this.status("NO CARRIER");
            this.reconnect();
        };

        this.ws.onerror = () => this.status("CARRIER ERROR");
    }

    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.term.write("\r\n*** CARRIER LOST - RELOAD TO DIAL AGAIN ***\r\n");
            return;
        }
        this.reconnectAttempts += 1;
        const delay = Math.min(1000 * this.reconnectAttempts, 5000);
        this.status(`REDIAL ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        setTimeout(() => this.connect(), delay);
    }

    sendKey(key) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ t: "key", d: key }));
            this.status("SENDING");
        }
    }

    status(text) {
        if (this.statusEl) this.statusEl.textContent = text;
    }

    toggleFastMode() {
        this.fastMode = !this.fastMode;
        this.status(this.fastMode ? "FAST MODE" : "2400 BAUD");
        if (this.ws) this.ws.close();
    }

    async healthCheck() {
        try {
            const response = await fetch("/healthz");
            if (!response.ok) return;
            const data = await response.json();
            if (this.onlineEl) this.onlineEl.textContent = `${data.callers} ONLINE`;
        } catch (err) { /* the board is allowed to be quiet */ }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.phosphor = new PhosphorClient();
});
