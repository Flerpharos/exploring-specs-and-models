"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.evaluateAST = evaluateAST;
exports.validateNumericResult = validateNumericResult;
const index_1 = require("./index");
const environment_1 = require("./environment");
function evaluateAST(node, env, context, sourceUnits) {
    if (node.type === "ValueLiteral") {
        const n = node;
        return new index_1.Value(n.magnitude, n.unit);
    }
    if (node.type === "Identifier") {
        const name = node.name;
        if (context === index_1.ParseContext.Value) {
            if (/^[A-Z]/.test(name)) {
                const val = env.variables.get(name);
                if (!val)
                    throw new environment_1.EvaluationError(`Error: unknown variable <${name}>.`);
                return val;
            }
            else if (/^[a-z]/.test(name)) {
                if (!env.units.has(name))
                    throw new environment_1.EvaluationError(`Error: unknown unit <${name}>.`);
                return new index_1.Value(1, { [name]: 1 });
            }
        }
        else if (context === index_1.ParseContext.Relationship) {
            if (/^[a-z]/.test(name) && sourceUnits && sourceUnits.includes(name)) {
                return new index_1.Value(1, { [name]: 1 });
            }
            throw new environment_1.EvaluationError(`Error: unknown unit <${name}>.`);
        }
        throw new environment_1.EvaluationError("Error: invalid formula.");
    }
    if (node.type === "UnaryOp") {
        const n = node;
        const operand = evaluateAST(n.operand, env, context, sourceUnits);
        if (n.op === "+") {
            return new index_1.Value(operand.magnitude, operand.unit);
        }
        else if (n.op === "-") {
            return new index_1.Value(-operand.magnitude, operand.unit);
        }
        else if (n.op === "[") {
            if (Object.keys(operand.unit).length > 0)
                throw new environment_1.EvaluationError("Error: log argument must be scalar.");
            if (operand.magnitude <= 0)
                throw new environment_1.EvaluationError("Error: log argument must be positive.");
            return new index_1.Value(Math.log(operand.magnitude), {});
        }
        else if (n.op === "]") {
            if (Object.keys(operand.unit).length > 0)
                throw new environment_1.EvaluationError("Error: exp argument must be scalar.");
            return new index_1.Value(Math.exp(operand.magnitude), {});
        }
    }
    if (node.type === "BinaryOp") {
        const n = node;
        const left = evaluateAST(n.left, env, context, sourceUnits);
        const right = evaluateAST(n.right, env, context, sourceUnits);
        if (n.op === "*") {
            return new index_1.Value(left.magnitude * right.magnitude, (0, index_1.multiplyUnit)(left.unit, right.unit));
        }
        else if (n.op === "/") {
            if (right.magnitude === 0)
                throw new environment_1.EvaluationError("Error: division by zero.");
            return new index_1.Value(left.magnitude / right.magnitude, (0, index_1.divideUnit)(left.unit, right.unit));
        }
        else if (n.op === "^") {
            if (Object.keys(right.unit).length > 0)
                throw new environment_1.EvaluationError("Error: exponent must be scalar.");
            // wait, spec says base can have any unit, but the numeric result must be real and finite.
            // Power of negative bases, fractional exponents etc might yield NaN.
            const mag = Math.pow(left.magnitude, right.magnitude);
            if (Number.isNaN(mag))
                throw new environment_1.EvaluationError("Error: numeric result is not real.");
            if (!Number.isFinite(mag))
                throw new environment_1.EvaluationError("Error: numeric result is not finite.");
            return new index_1.Value(mag, (0, index_1.powerUnit)(left.unit, right.magnitude));
        }
        else if (n.op === "+" || n.op === "-") {
            // Unification
            let a = left.magnitude;
            let b = right.magnitude;
            let targetUnit = left.unit;
            if ((0, index_1.serializeUnit)(left.unit) !== (0, index_1.serializeUnit)(right.unit)) {
                try {
                    const convertedRight = env.convert(right.magnitude, right.unit, left.unit);
                    b = convertedRight.magnitude;
                }
                catch {
                    try {
                        const convertedLeft = env.convert(left.magnitude, left.unit, right.unit);
                        a = convertedLeft.magnitude;
                        targetUnit = right.unit;
                    }
                    catch {
                        throw new environment_1.EvaluationError(`Error: cannot convert <${(0, index_1.serializeUnit)(right.unit)}> to <${(0, index_1.serializeUnit)(left.unit)}>.`);
                    }
                }
            }
            const mag = n.op === "+" ? a + b : a - b;
            return new index_1.Value(mag, targetUnit);
        }
    }
    throw new environment_1.EvaluationError("Error: invalid formula.");
}
function validateNumericResult(v) {
    if (Number.isNaN(v.magnitude))
        throw new environment_1.EvaluationError("Error: numeric result is not real.");
    if (!Number.isFinite(v.magnitude))
        throw new environment_1.EvaluationError("Error: numeric result is not finite.");
    for (const exponent of Object.values(v.unit)) {
        if (Number.isNaN(exponent))
            throw new environment_1.EvaluationError("Error: numeric result is not real.");
        if (!Number.isFinite(exponent))
            throw new environment_1.EvaluationError("Error: numeric result is not finite.");
    }
}
