import { ASTNode, ParseContext, UnitExpr, Value, UnitRelationship, normalizeUnit, multiplyUnit, divideUnit, powerUnit, serializeUnit, formatValue } from "./index";
import { Environment, EvaluationError } from "./environment";

export function evaluateAST(node: ASTNode, env: Environment, context: ParseContext, sourceUnits?: string[]): Value {
    if (node.type === "ValueLiteral") {
        const n = node as any;
        return new Value(n.magnitude, n.unit);
    }
    
    if (node.type === "Identifier") {
        const name = (node as any).name;
        
        if (context === ParseContext.Value) {
            if (/^[A-Z]/.test(name)) {
                const val = env.variables.get(name);
                if (!val) throw new EvaluationError(`Error: unknown variable <${name}>.`);
                return val;
            } else if (/^[a-z]/.test(name)) {
                if (!env.units.has(name)) throw new EvaluationError(`Error: unknown unit <${name}>.`);
                return new Value(1, { [name]: 1 });
            }
        } else if (context === ParseContext.Relationship) {
            if (/^[a-z]/.test(name) && sourceUnits && sourceUnits.includes(name)) {
                return new Value(1, { [name]: 1 });
            }
            throw new EvaluationError(`Error: unknown unit <${name}>.`);
        }
        throw new EvaluationError("Error: invalid formula.");
    }

    if (node.type === "UnaryOp") {
        const n = node as any;
        const operand = evaluateAST(n.operand, env, context, sourceUnits);
        
        if (n.op === "+") {
            return new Value(operand.magnitude, operand.unit);
        } else if (n.op === "-") {
            return new Value(-operand.magnitude, operand.unit);
        } else if (n.op === "[") {
            if (Object.keys(operand.unit).length > 0) throw new EvaluationError("Error: log argument must be scalar.");
            if (operand.magnitude <= 0) throw new EvaluationError("Error: log argument must be positive.");
            return new Value(Math.log(operand.magnitude), {});
        } else if (n.op === "]") {
            if (Object.keys(operand.unit).length > 0) throw new EvaluationError("Error: exp argument must be scalar.");
            return new Value(Math.exp(operand.magnitude), {});
        }
    }

    if (node.type === "BinaryOp") {
        const n = node as any;
        const left = evaluateAST(n.left, env, context, sourceUnits);
        const right = evaluateAST(n.right, env, context, sourceUnits);

        if (n.op === "*") {
            return new Value(left.magnitude * right.magnitude, multiplyUnit(left.unit, right.unit));
        } else if (n.op === "/") {
            if (right.magnitude === 0) throw new EvaluationError("Error: division by zero.");
            return new Value(left.magnitude / right.magnitude, divideUnit(left.unit, right.unit));
        } else if (n.op === "^") {
            if (Object.keys(right.unit).length > 0) throw new EvaluationError("Error: exponent must be scalar.");
            // wait, spec says base can have any unit, but the numeric result must be real and finite.
            // Power of negative bases, fractional exponents etc might yield NaN.
            const mag = Math.pow(left.magnitude, right.magnitude);
            if (Number.isNaN(mag)) throw new EvaluationError("Error: numeric result is not real.");
            if (!Number.isFinite(mag)) throw new EvaluationError("Error: numeric result is not finite.");
            return new Value(mag, powerUnit(left.unit, right.magnitude));
        } else if (n.op === "+" || n.op === "-") {
            // Unification
            let a = left.magnitude;
            let b = right.magnitude;
            let targetUnit = left.unit;

            if (serializeUnit(left.unit) !== serializeUnit(right.unit)) {
                try {
                    const convertedRight = env.convert(right.magnitude, right.unit, left.unit);
                    b = convertedRight.magnitude;
                } catch {
                    try {
                        const convertedLeft = env.convert(left.magnitude, left.unit, right.unit);
                        a = convertedLeft.magnitude;
                        targetUnit = right.unit;
                    } catch {
                        throw new EvaluationError(`Error: cannot convert <${serializeUnit(right.unit)}> to <${serializeUnit(left.unit)}>.`);
                    }
                }
            }

            const mag = n.op === "+" ? a + b : a - b;
            return new Value(mag, targetUnit);
        }
    }

    throw new EvaluationError("Error: invalid formula.");
}

export function validateNumericResult(v: Value) {
    if (Number.isNaN(v.magnitude)) throw new EvaluationError("Error: numeric result is not real.");
    if (!Number.isFinite(v.magnitude)) throw new EvaluationError("Error: numeric result is not finite.");
    for (const exponent of Object.values(v.unit)) {
        if (Number.isNaN(exponent)) throw new EvaluationError("Error: numeric result is not real.");
        if (!Number.isFinite(exponent)) throw new EvaluationError("Error: numeric result is not finite.");
    }
}
