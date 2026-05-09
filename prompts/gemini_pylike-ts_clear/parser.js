"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Parser = exports.ParseError = void 0;
exports.parseInteger = parseInteger;
exports.parseUnitFactor = parseUnitFactor;
exports.parseUnitSection = parseUnitSection;
exports.parseFormulaExpr = parseFormulaExpr;
exports.parsePrefix = parsePrefix;
exports.parseValueFormula = parseValueFormula;
exports.parseRelationshipFormula = parseRelationshipFormula;
exports.parseUnitExpression = parseUnitExpression;
exports.parseUnitProduct = parseUnitProduct;
exports.parseUnitPower = parseUnitPower;
exports.parseUnitPrimary = parseUnitPrimary;
const index_1 = require("./index");
class ParseError extends Error {
    constructor(message) {
        super(message);
    }
}
exports.ParseError = ParseError;
class Parser {
    tokens;
    pos;
    constructor(tokens) {
        this.tokens = tokens;
        this.pos = 0;
    }
    peek(offset = 0) {
        if (this.pos + offset >= this.tokens.length) {
            return this.tokens[this.tokens.length - 1];
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
                return (0, index_1.powerUnit)(u, power);
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
            u = (0, index_1.multiplyUnit)(u, right);
        }
        else {
            u = (0, index_1.divideUnit)(u, right);
        }
    }
    return u;
}
function parseFormulaExpr(p, context, precedence = 0) {
    let left = parsePrefix(p, context);
    while (true) {
        const t = p.peek();
        if (t.type === "EOF")
            break;
        const opPrec = getBinaryPrecedence(t.value);
        if (opPrec === 0 || opPrec < precedence) {
            break;
        }
        // Check associativity. ^ is right-associative. *, /, +, - are left-associative.
        const assoc = getAssociativity(t.value);
        const nextPrec = assoc === "right" ? opPrec : opPrec + 1;
        const opToken = p.consume();
        const right = parseFormulaExpr(p, context, nextPrec);
        // Validation for relationship context
        if (context === index_1.ParseContext.Relationship) {
            if (opToken.value === "+" || opToken.value === "-") {
                throw new ParseError("Error: invalid formula.");
            }
        }
        left = {
            type: "BinaryOp",
            op: opToken.value,
            left,
            right
        };
    }
    return left;
}
function getBinaryPrecedence(op) {
    switch (op) {
        case "+":
        case "-": return 1;
        case "*":
        case "/": return 2;
        case "^": return 3;
        default: return 0;
    }
}
function getAssociativity(op) {
    if (op === "^")
        return "right";
    return "left";
}
function parsePrefix(p, context) {
    const t = p.peek();
    if (t.value === "+" || t.value === "-" || t.value === "[" || t.value === "]") {
        if (context === index_1.ParseContext.Relationship && (t.value === "[" || t.value === "]")) {
            throw new ParseError("Error: invalid formula.");
        }
        p.consume();
        const operand = parseFormulaExpr(p, context, 4); // prefix precedence is 4, right associative
        return {
            type: "UnaryOp",
            op: t.value,
            operand
        };
    }
    if (t.type === "NUMBER") {
        p.consume();
        const num = parseFloat(t.value);
        let u = {};
        const next = p.peek();
        if (next.type === "UNIT" || next.value === "(") {
            const savedPos = p.pos;
            try {
                u = parseUnitSection(p);
            }
            catch {
                p.pos = savedPos;
            }
        }
        return { type: "ValueLiteral", magnitude: num, unit: u };
    }
    if (t.type === "UNIT" || t.type === "VAR") {
        p.consume();
        return { type: "Identifier", name: t.value };
    }
    if (t.value === "(") {
        p.consume();
        const expr = parseFormulaExpr(p, context, 0);
        if (p.peek().value !== ")") {
            throw new ParseError("Error: invalid formula.");
        }
        p.consume();
        return expr;
    }
    throw new ParseError("Error: invalid formula.");
}
// Full entry points
function parseValueFormula(p) {
    const ast = parseFormulaExpr(p, index_1.ParseContext.Value);
    if (p.peek().type !== "EOF") {
        throw new ParseError("Error: invalid formula.");
    }
    return ast;
}
function parseRelationshipFormula(p) {
    const ast = parseFormulaExpr(p, index_1.ParseContext.Relationship);
    if (p.peek().type !== "EOF") {
        throw new ParseError("Error: invalid formula.");
    }
    return ast;
}
// Unit parsing (Output Units, Relationship Basis)
function parseUnitExpression(p) {
    const u = parseUnitProduct(p);
    if (p.peek().type !== "EOF") {
        throw new ParseError("Error: invalid output unit."); // Wait, context specific error. Handled higher up?
    }
    return u;
}
function parseUnitProduct(p) {
    let u = parseUnitPower(p);
    while (p.peek().value === "*" || p.peek().value === "/") {
        const op = p.consume().value;
        const right = parseUnitPower(p);
        if (op === "*") {
            u = (0, index_1.multiplyUnit)(u, right);
        }
        else {
            u = (0, index_1.divideUnit)(u, right);
        }
    }
    return u;
}
function parseUnitPower(p) {
    const u = parseUnitPrimary(p);
    if (p.peek().value === "^") {
        p.consume();
        const power = parseInteger(p);
        return (0, index_1.powerUnit)(u, power);
    }
    return u;
}
function parseUnitPrimary(p) {
    const t = p.peek();
    if (t.type === "UNIT") {
        p.consume();
        return { [t.value]: 1 };
    }
    else if (t.value === "1") {
        // Wait, "1" is a NUMBER in tokenizer, but unit-primary grammar allows "1"!
        if (t.type === "NUMBER" && t.value === "1") {
            p.consume();
            return {};
        }
    }
    else if (t.value === "(") {
        p.consume();
        const u = parseUnitProduct(p);
        if (p.peek().value !== ")") {
            throw new ParseError("Error: invalid formula.");
        }
        p.consume();
        return u;
    }
    throw new ParseError("Error: invalid formula.");
}
