"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.executeCommand = executeCommand;
const environment_1 = require("./environment");
const parser_1 = require("./parser");
const tokenizer_1 = require("./tokenizer");
const evaluator_1 = require("./evaluator");
const index_1 = require("./index");
function executeCommand(line, env) {
    if (line.trim() === "")
        return null;
    const originalEnv = cloneEnvironment(env);
    try {
        if (line.startsWith("unit:")) {
            const payload = line.slice(5).trim();
            if (!/^[a-z][a-z_]*$/.test(payload)) {
                throw new Error("Error: invalid unit name.");
            }
            env.units.add(payload);
            return null;
        }
        if (line.startsWith("set:")) {
            const payload = line.slice(4);
            const colonIdx = payload.indexOf(":");
            if (colonIdx === -1)
                throw new Error("Error: invalid command syntax.");
            const varId = payload.slice(0, colonIdx).trim();
            const formulaStr = payload.slice(colonIdx + 1).trim();
            if (!/^[A-Z][A-Z_]*$/.test(varId))
                throw new Error("Error: invalid variable name.");
            if (formulaStr.length === 0)
                throw new Error("Error: invalid command syntax.");
            const tokens = (0, tokenizer_1.tokenize)(formulaStr);
            const parser = new parser_1.Parser(tokens);
            const ast = (0, parser_1.parseValueFormula)(parser);
            const val = (0, evaluator_1.evaluateAST)(ast, env, index_1.ParseContext.Value);
            (0, evaluator_1.validateNumericResult)(val);
            env.variables.set(varId, val);
            return null;
        }
        if (line.startsWith("relate:")) {
            const payload = line.slice(7);
            const firstColon = payload.indexOf(":");
            if (firstColon === -1)
                throw new Error("Error: invalid command syntax.");
            const secondColon = payload.indexOf(":", firstColon + 1);
            if (secondColon === -1)
                throw new Error("Error: invalid command syntax.");
            const targetId = payload.slice(0, firstColon).trim();
            const sourceListStr = payload.slice(firstColon + 1, secondColon).trim();
            const formulaStr = payload.slice(secondColon + 1).trim();
            if (!/^[a-z][a-z_]*$/.test(targetId))
                throw new Error("Error: invalid unit name.");
            const sourceList = sourceListStr.split(",").map(s => s.trim());
            if (sourceList.length === 0)
                throw new Error("Error: invalid unit list.");
            const sourceSet = new Set();
            for (const s of sourceList) {
                if (s === "")
                    throw new Error("Error: invalid unit list.");
                if (!/^[a-z][a-z_]*$/.test(s))
                    throw new Error("Error: invalid unit list.");
                if (sourceSet.has(s))
                    throw new Error("Error: invalid unit list.");
                if (!env.units.has(s))
                    throw new Error(`Error: unknown unit <${s}>.`); // wait, spec says "must be a declared UnitId" for sources. What error? "Error: unknown unit <name>."? Spec: "each item must be a declared UnitId". Let's check Error list. Wait. Error list: "Error: invalid unit list." No, "Error: unknown unit <name>." ? Wait, it just says "each item must be a declared UnitId". Let's throw "Error: invalid unit list." if not declared, or maybe "Error: unknown unit"? Spec says "reject ... each item must be a declared UnitId". Let's just throw "Error: invalid unit list." to be safe. Wait! "Error: unknown unit <name>." is in the error list. Let's use that.
                sourceSet.add(s);
            }
            if (sourceSet.has(targetId))
                throw new Error("Error: invalid unit list.");
            if (formulaStr.length === 0)
                throw new Error("Error: invalid command syntax.");
            const tokens = (0, tokenizer_1.tokenize)(formulaStr);
            const parser = new parser_1.Parser(tokens);
            const ast = (0, parser_1.parseRelationshipFormula)(parser);
            const val = (0, evaluator_1.evaluateAST)(ast, env, index_1.ParseContext.Relationship, sourceList);
            (0, evaluator_1.validateNumericResult)(val);
            if (val.magnitude === 0)
                throw new Error("Error: invalid relationship.");
            // basis must contain ONLY units from source unit list.
            for (const u of Object.keys(val.unit)) {
                if (!sourceSet.has(u))
                    throw new Error("Error: invalid relationship.");
            }
            env.units.add(targetId);
            env.relationships.set(targetId, {
                target: targetId,
                factor: val.magnitude,
                basis: val.unit
            });
            return null;
        }
        if (line.startsWith("evaluate:")) {
            const payload = line.slice(9);
            const lastColon = payload.lastIndexOf(":");
            let valueFormulaStr = payload.trim();
            let outputFormulaStr = "";
            let hasOutput = false;
            if (lastColon !== -1) {
                valueFormulaStr = payload.slice(0, lastColon).trim();
                outputFormulaStr = payload.slice(lastColon + 1).trim();
                hasOutput = true;
            }
            if (valueFormulaStr.length === 0)
                throw new Error("Error: invalid command syntax.");
            if (hasOutput && outputFormulaStr.length === 0)
                throw new Error("Error: invalid command syntax.");
            let targetUnit = null;
            if (hasOutput) {
                const tokens = (0, tokenizer_1.tokenize)(outputFormulaStr);
                const parser = new parser_1.Parser(tokens);
                try {
                    targetUnit = (0, parser_1.parseUnitExpression)(parser);
                }
                catch (e) {
                    if (e.message.startsWith("Error: invalid formula.")) {
                        throw new Error("Error: invalid output unit.");
                    }
                    throw e;
                }
                // check if targetUnit uses undeclared units
                for (const u of Object.keys(targetUnit)) {
                    if (!env.units.has(u))
                        throw new Error(`Error: unknown unit <${u}>.`);
                }
            }
            const tokens = (0, tokenizer_1.tokenize)(valueFormulaStr);
            const parser = new parser_1.Parser(tokens);
            const ast = (0, parser_1.parseValueFormula)(parser);
            const val = (0, evaluator_1.evaluateAST)(ast, env, index_1.ParseContext.Value);
            (0, evaluator_1.validateNumericResult)(val);
            if (targetUnit) {
                const converted = env.convert(val.magnitude, val.unit, targetUnit);
                (0, evaluator_1.validateNumericResult)(converted);
                return `${converted.magnitude} ${(0, index_1.serializeUnit)(targetUnit)}`;
            }
            else {
                return `${val.magnitude} ${(0, index_1.serializeUnit)(val.unit)}`;
            }
        }
        throw new Error("Error: unknown command.");
    }
    catch (e) {
        restoreEnvironment(env, originalEnv);
        if (e.message.startsWith("Error:")) {
            return e.message;
        }
        return "Error: " + e.message;
    }
}
function cloneEnvironment(env) {
    const clone = new environment_1.Environment();
    clone.units = new Set(env.units);
    clone.variables = new Map(env.variables);
    clone.relationships = new Map(env.relationships);
    return clone;
}
function restoreEnvironment(target, source) {
    target.units = new Set(source.units);
    target.variables = new Map(source.variables);
    target.relationships = new Map(source.relationships);
}
