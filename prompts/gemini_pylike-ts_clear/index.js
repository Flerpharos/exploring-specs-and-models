"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Parser = exports.ParseContext = exports.UnitRelationship = exports.Value = void 0;
exports.normalizeUnit = normalizeUnit;
exports.multiplyUnit = multiplyUnit;
exports.divideUnit = divideUnit;
exports.powerUnit = powerUnit;
exports.serializeUnit = serializeUnit;
exports.formatValue = formatValue;
class Value {
    magnitude;
    unit;
    constructor(magnitude, unit) {
        this.magnitude = magnitude;
        this.unit = unit;
    }
}
exports.Value = Value;
class UnitRelationship {
    target;
    factor;
    basis;
    constructor(target, factor, basis) {
        this.target = target;
        this.factor = factor;
        this.basis = basis;
    }
}
exports.UnitRelationship = UnitRelationship;
// Unit Math
function normalizeUnit(u) {
    const res = {};
    for (const [k, v] of Object.entries(u)) {
        if (v !== 0) {
            res[k] = v;
        }
    }
    return res;
}
function multiplyUnit(u, v) {
    const res = { ...u };
    for (const [key, val] of Object.entries(v)) {
        res[key] = (res[key] || 0) + val;
    }
    return normalizeUnit(res);
}
function divideUnit(u, v) {
    const res = { ...u };
    for (const [key, val] of Object.entries(v)) {
        res[key] = (res[key] || 0) - val;
    }
    return normalizeUnit(res);
}
function powerUnit(u, n) {
    const res = {};
    for (const [key, val] of Object.entries(u)) {
        res[key] = val * n;
    }
    return normalizeUnit(res);
}
function serializeUnit(u) {
    const uNorm = normalizeUnit(u);
    const keys = Object.keys(uNorm).sort();
    const num = [];
    const den = [];
    for (const k of keys) {
        const v = uNorm[k];
        if (v > 0) {
            num.push(v === 1 ? k : `${k}^${v}`);
        }
        else if (v < 0) {
            const absV = -v;
            den.push(absV === 1 ? k : `${k}^${absV}`);
        }
    }
    if (num.length === 0 && den.length === 0) {
        return "1";
    }
    let res = "";
    if (num.length > 0) {
        res += num.join("*");
    }
    else if (den.length > 0) {
        res += "1";
    }
    if (den.length > 0) {
        res += "/" + den.join("/");
    }
    return res;
}
function formatValue(val) {
    return `${val.magnitude} ${serializeUnit(val.unit)}`;
}
// Context Enum
var ParseContext;
(function (ParseContext) {
    ParseContext[ParseContext["Value"] = 0] = "Value";
    ParseContext[ParseContext["Relationship"] = 1] = "Relationship";
    ParseContext[ParseContext["OutputUnit"] = 2] = "OutputUnit";
})(ParseContext || (exports.ParseContext = ParseContext = {}));
// Parser
class Parser {
    tokens;
    pos;
    constructor(tokens) {
        this.tokens = tokens;
        this.pos = 0;
    }
    peek(offset = 0) {
        if (this.pos + offset >= this.tokens.length) {
            return this.tokens[this.tokens.length - 1]; // EOF
        }
        return this.tokens[this.pos + offset];
    }
    consume() {
        const t = this.peek();
        this.pos++;
        return t;
    }
    match(type, value) {
        const t = this.peek();
        if (t.type === type && (value === undefined || t.value === value)) {
            this.consume();
            return true;
        }
        return false;
    }
}
exports.Parser = Parser;
