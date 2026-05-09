"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.tokenize = tokenize;
function tokenize(text) {
    const tokens = [];
    let i = 0;
    while (i < text.length) {
        const s = text.slice(i);
        let m;
        if ((m = s.match(/^\s+/))) {
            i += m[0].length;
            continue;
        }
        if ((m = s.match(/^(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?/))) {
            tokens.push({ type: "NUMBER", value: m[0] });
            i += m[0].length;
            continue;
        }
        if ((m = s.match(/^[a-z][a-z_]*/))) {
            tokens.push({ type: "UNIT", value: m[0] });
            i += m[0].length;
            continue;
        }
        if ((m = s.match(/^[A-Z][A-Z_]*/))) {
            tokens.push({ type: "VAR", value: m[0] });
            i += m[0].length;
            continue;
        }
        if ((m = s.match(/^[+\-*/^()[\]]/))) {
            tokens.push({ type: "OP", value: m[0] });
            i += m[0].length;
            continue;
        }
        throw new Error("invalid token");
    }
    tokens.push({ type: "EOF", value: "" });
    return tokens;
}
