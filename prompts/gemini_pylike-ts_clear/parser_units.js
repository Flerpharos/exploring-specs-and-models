"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ParseError = void 0;
exports.parseInteger = parseInteger;
exports.parseUnitFactor = parseUnitFactor;
exports.parseUnitSection = parseUnitSection;
class ParseError extends Error {
    constructor(message) {
        super(message);
    }
}
exports.ParseError = ParseError;
function parseInteger(p) {
    let sign = 1;
    if (p.peek().value === "+") {
        p.consume();
    }
    else if (p.peek().value === "-") {
        p.consume();
        sign = -1;
    }
    const t = p.peek();
    if (t.type === "NUMBER" && /^\d+$/.test(t.value)) {
        p.consume();
        return sign * parseInt(t.value, 10);
    }
    throw new ParseError("Error: invalid formula.");
}
function parseUnitFactor(p) {
    const t = p.peek();
    if (t.type === "UNIT") {
        p.consume();
        let power = 1;
        if (p.peek().value === "^") {
            p.consume();
            power = parseInteger(p);
        }
        return { [t.value]: power };
    }
    else if (t.value === "(") {
        // Need to be careful. Is this a unit-section in parentheses, or a formula?
        // In unit-section parsing, we can have "(" unit-section ")"
        // But what if it's not a unit section? 
        // We only attempt parseUnitFactor if we KNOW we are in unit attachment.
        const savedPos = p.pos;
        p.consume();
        try {
            const u = parseUnitSection(p);
            if (p.peek().value === ")") {
                p.consume();
                let power = 1;
                if (p.peek().value === "^") {
                    p.consume();
                    power = parseInteger(p);
                }
                return powerUnit(u, power);
            }
        }
        catch {
            // fallthrough
        }
        p.pos = savedPos;
        return null;
    }
    return null;
}
function parseUnitSection(p) {
    let u = parseUnitFactor(p);
    if (!u) {
        throw new ParseError("Error: invalid formula.");
    }
    while (p.peek().value === "*" || p.peek().value === "/") {
        const op = p.consume().value;
        const right = parseUnitFactor(p);
        if (!right) {
            throw new ParseError("Error: invalid formula.");
        }
        if (op === "*") {
            u = multiplyUnit(u, right);
        }
        else {
            u = divideUnit(u, right);
        }
    }
    return u;
}
