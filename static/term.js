// PHOSPHOR terminal renderer.
// A deliberately small ANSI parser: the server only speaks the subset below.
//   ESC[2J        clear
//   ESC[H         home
//   ESC[<r>;<c>H  move cursor (1-based)
//   ESC[<n>m      colour: 0/39 reset, 31 red, 32 green, 33 amber, 37 grey
//   \r \n         carriage return / line feed
// Everything else is printed at the cursor.

const COLORS = { 0: "green", 31: "red", 32: "green", 33: "amber", 37: "grey", 39: "green" };

class PhosphorTerm {
    constructor(element, { cols = 80, rows = 24 } = {}) {
        this.el = element;
        this.cols = cols;
        this.rows = rows;
        this.grid = [];
        this.cursor = { row: 0, col: 0 };
        this.color = "green";
        this.onData = null;
        this.clear();
    }

    clear() {
        this.grid = [];
        for (let r = 0; r < this.rows; r++) {
            const row = [];
            for (let c = 0; c < this.cols; c++) row.push({ ch: " ", fg: "green" });
            this.grid.push(row);
        }
        this.cursor = { row: 0, col: 0 };
        this.color = "green";
    }

    focus() { this.el.tabIndex = 0; this.el.focus(); }

    write(data) {
        let i = 0;
        while (i < data.length) {
            const ch = data[i];
            if (ch === "\x1b" && data[i + 1] === "[") {
                const end = data.indexOf("H", i);
                const endM = data.indexOf("m", i);
                const endJ = data.indexOf("J", i);
                const candidates = [end, endM, endJ].filter((n) => n !== -1).sort((a, b) => a - b);
                if (candidates.length === 0) break;
                const stop = candidates[0];
                const params = data.slice(i + 2, stop);
                const final = data[stop];
                this.control(params, final);
                i = stop + 1;
                continue;
            }
            if (ch === "\r") { this.cursor.col = 0; i++; continue; }
            if (ch === "\n") { this.cursor.row = Math.min(this.rows - 1, this.cursor.row + 1); i++; continue; }
            this.put(ch);
            i++;
        }
        this.render();
    }

    control(params, final) {
        if (final === "J") { this.clear(); return; }
        if (final === "H") {
            if (!params) { this.cursor.row = 0; this.cursor.col = 0; return; }
            const [r, c] = params.split(";").map((n) => parseInt(n, 10) || 1);
            this.cursor.row = Math.min(this.rows - 1, Math.max(0, r - 1));
            this.cursor.col = Math.min(this.cols - 1, Math.max(0, c - 1));
            return;
        }
        if (final === "m") {
            const code = parseInt(params || "0", 10);
            this.color = COLORS[code] || this.color;
        }
    }

    put(ch) {
        if (this.cursor.row < 0 || this.cursor.row >= this.rows) return;
        if (this.cursor.col >= this.cols) { this.cursor.col = 0; this.cursor.row = Math.min(this.rows - 1, this.cursor.row + 1); }
        this.grid[this.cursor.row][this.cursor.col] = { ch, fg: this.color };
        this.cursor.col++;
    }

    render() {
        const escape = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        const out = [];
        for (let r = 0; r < this.rows; r++) {
            const row = this.grid[r];
            let buffer = "";
            let run = row[0].fg;
            let html = "";
            const flush = () => {
                if (buffer) html += `<span class="fg-${run}">${escape(buffer)}</span>`;
                buffer = "";
            };
            for (let c = 0; c < this.cols; c++) {
                const cell = row[c];
                if (cell.fg !== run) { flush(); run = cell.fg; }
                buffer += cell.ch;
            }
            flush();
            out.push(html);
        }
        this.el.innerHTML = out.join("\n");
    }
}

window.PhosphorTerm = PhosphorTerm;
