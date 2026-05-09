import { Token, tokenize } from "./tokenizer";

export type UnitExpr = Record<string, number>;

export class Value {
    magnitude: number;
    unit: UnitExpr;

    constructor(magnitude: number, unit: UnitExpr) {
        this.magnitude = magnitude;
        this.unit = unit;
    }
}

export class UnitRelationship {
    target: string;
    factor: number;
    basis: UnitExpr;

    constructor(target: string, factor: number, basis: UnitExpr) {
        this.target = target;
        this.factor = factor;
        this.basis = basis;
    }
}

// Unit Math
export function normalizeUnit(u: UnitExpr): UnitExpr {
    const res: UnitExpr = {};
    for (const [k, v] of Object.entries(u)) {
        if (v !== 0) {
            res[k] = v;
        }
    }
    return res;
}

export function multiplyUnit(u: UnitExpr, v: UnitExpr): UnitExpr {
    const res = { ...u };
    for (const [key, val] of Object.entries(v)) {
        res[key] = (res[key] || 0) + val;
    }
    return normalizeUnit(res);
}

export function divideUnit(u: UnitExpr, v: UnitExpr): UnitExpr {
    const res = { ...u };
    for (const [key, val] of Object.entries(v)) {
        res[key] = (res[key] || 0) - val;
    }
    return normalizeUnit(res);
}

export function powerUnit(u: UnitExpr, n: number): UnitExpr {
    const res: UnitExpr = {};
    for (const [key, val] of Object.entries(u)) {
        res[key] = val * n;
    }
    return normalizeUnit(res);
}

export function serializeUnit(u: UnitExpr): string {
    const uNorm = normalizeUnit(u);
    const keys = Object.keys(uNorm).sort();
    const num: string[] = [];
    const den: string[] = [];
    
    for (const k of keys) {
        const v = uNorm[k];
        if (v > 0) {
            num.push(v === 1 ? k : `${k}^${v}`);
        } else if (v < 0) {
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
    } else if (den.length > 0) {
        res += "1";
    }

    if (den.length > 0) {
        res += "/" + den.join("/");
    }
    
    return res;
}

export function formatValue(val: Value): string {
    return `${val.magnitude} ${serializeUnit(val.unit)}`;
}

// AST Nodes
export interface ASTNode { type: string; }
export interface ValueLiteralNode extends ASTNode { type: 'ValueLiteral'; magnitude: number; unit: UnitExpr; }
export interface IdentifierNode extends ASTNode { type: 'Identifier'; name: string; }
export interface UnaryOpNode extends ASTNode { type: 'UnaryOp'; op: string; operand: ASTNode; }
export interface BinaryOpNode extends ASTNode { type: 'BinaryOp'; op: string; left: ASTNode; right: ASTNode; }

// Context Enum
export enum ParseContext {
    Value,
    Relationship,
    OutputUnit
}

// Parser
export class Parser {
    tokens: Token[];
    pos: number;

    constructor(tokens: Token[]) {
        this.tokens = tokens;
        this.pos = 0;
    }

    peek(offset = 0): Token {
        if (this.pos + offset >= this.tokens.length) {
            return this.tokens[this.tokens.length - 1]; // EOF
        }
        return this.tokens[this.pos + offset];
    }

    consume(): Token {
        const t = this.peek();
        this.pos++;
        return t;
    }

    match(type: string, value?: string): boolean {
        const t = this.peek();
        if (t.type === type && (value === undefined || t.value === value)) {
            this.consume();
            return true;
        }
        return false;
    }

    // parsing logic to be filled
}

