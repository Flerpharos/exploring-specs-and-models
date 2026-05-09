import { Token } from "./tokenizer";
import { UnitExpr, multiplyUnit, divideUnit, powerUnit, ParseContext, ASTNode } from "./index";

export class ParseError extends Error {
    constructor(message: string) {
        super(message);
    }
}

export class Parser {
    tokens: Token[];
    pos: number;

    constructor(tokens: Token[]) {
        this.tokens = tokens;
        this.pos = 0;
    }

    peek(offset = 0): Token {
        if (this.pos + offset >= this.tokens.length) {
            return this.tokens[this.tokens.length - 1];
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
}

export function parseInteger(p: Parser): number {
    let sign = 1;
    if (p.peek().value === "+") {
        p.consume();
    } else if (p.peek().value === "-") {
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

export function parseUnitFactor(p: Parser): UnitExpr | null {
    const t = p.peek();
    if (t.type === "UNIT") {
        p.consume();
        let power = 1;
        if (p.peek().value === "^") {
            p.consume();
            power = parseInteger(p);
        }
        return { [t.value]: power };
    } else if (t.value === "(") {
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
        } catch {
            // fallthrough
        }
        p.pos = savedPos;
        return null;
    }
    return null;
}

export function parseUnitSection(p: Parser): UnitExpr {
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
        } else {
            u = divideUnit(u, right);
        }
    }
    return u;
}

export function parseFormulaExpr(p: Parser, context: ParseContext, precedence: number = 0): ASTNode {
    let left = parsePrefix(p, context);

    while (true) {
        const t = p.peek();
        if (t.type === "EOF") break;

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
        if (context === ParseContext.Relationship) {
            if (opToken.value === "+" || opToken.value === "-") {
                throw new ParseError("Error: invalid formula.");
            }
        }

        left = {
            type: "BinaryOp",
            op: opToken.value,
            left,
            right
        } as ASTNode;
    }

    return left;
}

function getBinaryPrecedence(op: string): number {
    switch (op) {
        case "+": case "-": return 1;
        case "*": case "/": return 2;
        case "^": return 3;
        default: return 0;
    }
}

function getAssociativity(op: string): string {
    if (op === "^") return "right";
    return "left";
}

export function parsePrefix(p: Parser, context: ParseContext): ASTNode {
    const t = p.peek();

    if (t.value === "+" || t.value === "-" || t.value === "[" || t.value === "]") {
        if (context === ParseContext.Relationship && (t.value === "[" || t.value === "]")) {
            throw new ParseError("Error: invalid formula.");
        }
        p.consume();
        const operand = parseFormulaExpr(p, context, 4); // prefix precedence is 4, right associative
        return {
            type: "UnaryOp",
            op: t.value,
            operand
        } as ASTNode;
    }

    if (t.type === "NUMBER") {
        p.consume();
        const num = parseFloat(t.value);
        let u: UnitExpr = {};
        
        const next = p.peek();
        if (next.type === "UNIT" || next.value === "(") {
            const savedPos = p.pos;
            try {
                u = parseUnitSection(p);
            } catch {
                p.pos = savedPos;
            }
        }
        return { type: "ValueLiteral", magnitude: num, unit: u } as ASTNode;
    }

    if (t.type === "UNIT" || t.type === "VAR") {
        p.consume();
        return { type: "Identifier", name: t.value } as ASTNode;
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
export function parseValueFormula(p: Parser): ASTNode {
    const ast = parseFormulaExpr(p, ParseContext.Value);
    if (p.peek().type !== "EOF") {
        throw new ParseError("Error: invalid formula.");
    }
    return ast;
}

export function parseRelationshipFormula(p: Parser): ASTNode {
    const ast = parseFormulaExpr(p, ParseContext.Relationship);
    if (p.peek().type !== "EOF") {
        throw new ParseError("Error: invalid formula.");
    }
    return ast;
}

// Unit parsing (Output Units, Relationship Basis)
export function parseUnitExpression(p: Parser): UnitExpr {
    const u = parseUnitProduct(p);
    if (p.peek().type !== "EOF") {
        throw new ParseError("Error: invalid output unit."); // Wait, context specific error. Handled higher up?
    }
    return u;
}

export function parseUnitProduct(p: Parser): UnitExpr {
    let u = parseUnitPower(p);
    while (p.peek().value === "*" || p.peek().value === "/") {
        const op = p.consume().value;
        const right = parseUnitPower(p);
        if (op === "*") {
            u = multiplyUnit(u, right);
        } else {
            u = divideUnit(u, right);
        }
    }
    return u;
}

export function parseUnitPower(p: Parser): UnitExpr {
    const u = parseUnitPrimary(p);
    if (p.peek().value === "^") {
        p.consume();
        const power = parseInteger(p);
        return powerUnit(u, power);
    }
    return u;
}

export function parseUnitPrimary(p: Parser): UnitExpr {
    const t = p.peek();
    if (t.type === "UNIT") {
        p.consume();
        return { [t.value]: 1 };
    } else if (t.value === "1") {
        // Wait, "1" is a NUMBER in tokenizer, but unit-primary grammar allows "1"!
        if (t.type === "NUMBER" && t.value === "1") {
            p.consume();
            return {};
        }
    } else if (t.value === "(") {
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
