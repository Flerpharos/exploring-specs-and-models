import { ASTNode, ParseContext, UnitExpr, Value, UnitRelationship, normalizeUnit, multiplyUnit, divideUnit, powerUnit, serializeUnit, formatValue } from "./index";

export class EvaluationError extends Error {
    constructor(message: string) {
        super(message);
    }
}

interface State {
    u: UnitExpr;
    uStr: string;
    mag: number;
    pathKey: string;
}

interface Transition {
    state: State;
    relTarget: string;
    isForward: boolean;
}

export class Environment {
    units: Set<string>;
    variables: Map<string, Value>;
    relationships: Map<string, UnitRelationship>;

    constructor() {
        this.units = new Set();
        this.variables = new Map();
        this.relationships = new Map();
    }

    convert(magnitude: number, source: UnitExpr, target: UnitExpr): Value {
        const sourceStr = serializeUnit(source);
        const targetStr = serializeUnit(target);
        
        if (sourceStr === targetStr) {
            return new Value(magnitude, target);
        }

        let currentLevel: State[] = [{
            u: source,
            uStr: sourceStr,
            mag: magnitude,
            pathKey: sourceStr
        }];
        
        const visited = new Set<string>();
        visited.add(sourceStr);

        while (currentLevel.length > 0) {
            const nextLevelMap = new Map<string, Transition>();

            for (const state of currentLevel) {
                for (const rel of this.relationships.values()) {
                    // Forward: target -> basis
                    const targetPower = state.u[rel.target] || 0;
                    if (targetPower !== 0) {
                        const newU = { ...state.u };
                        delete newU[rel.target];
                        const poweredBasis = powerUnit(rel.basis, targetPower);
                        const nextU = multiplyUnit(newU, poweredBasis);
                        const nextUStr = serializeUnit(nextU);
                        
                        if (!visited.has(nextUStr)) {
                            // JS Math.pow handles real numbers properly
                            const factorMag = Math.pow(rel.factor, targetPower);
                            const nextMag = state.mag * factorMag;
                            if (Number.isFinite(nextMag)) { // we only allow valid finite steps but defer error? "applying a relationship would produce a non-finite numeric scale -> Error: invalid relationship."
                                const nextState: State = {
                                    u: nextU,
                                    uStr: nextUStr,
                                    mag: nextMag,
                                    pathKey: state.pathKey + "," + nextUStr
                                };
                                this.addTransition(nextLevelMap, nextState, rel.target, true);
                            } else {
                                throw new EvaluationError("Error: invalid relationship.");
                            }
                        }
                    }

                    // Reverse: basis -> target
                    // For every unit x in basis, r[x] = U[x] / basis[x]
                    let allSameSign = true;
                    let sign = 0;
                    let minAbsE = Infinity;
                    let hasBasisMatch = false;

                    for (const [x, basisPower] of Object.entries(rel.basis)) {
                        const uPower = state.u[x] || 0;
                        const r = uPower / basisPower;
                        if (r !== 0) {
                            hasBasisMatch = true;
                            const rSign = Math.sign(r);
                            if (sign === 0) {
                                sign = rSign;
                            } else if (sign !== rSign) {
                                allSameSign = false;
                                break;
                            }
                            minAbsE = Math.min(minAbsE, Math.abs(r));
                        }
                    }

                    if (hasBasisMatch && allSameSign && sign !== 0 && minAbsE !== Infinity) {
                        const e = sign * minAbsE;
                        const basisE = powerUnit(rel.basis, e);
                        let nextU = divideUnit(state.u, basisE);
                        nextU[rel.target] = (nextU[rel.target] || 0) + e;
                        nextU = normalizeUnit(nextU);
                        const nextUStr = serializeUnit(nextU);

                        if (!visited.has(nextUStr)) {
                            const factorMag = Math.pow(rel.factor, -e);
                            const nextMag = state.mag * factorMag;
                            if (Number.isFinite(nextMag)) {
                                const nextState: State = {
                                    u: nextU,
                                    uStr: nextUStr,
                                    mag: nextMag,
                                    pathKey: state.pathKey + "," + nextUStr
                                };
                                this.addTransition(nextLevelMap, nextState, rel.target, false);
                            } else {
                                throw new EvaluationError("Error: invalid relationship.");
                            }
                        }
                    }
                }
            }

            if (nextLevelMap.has(targetStr)) {
                return new Value(nextLevelMap.get(targetStr)!.state.mag, target);
            }

            currentLevel = [];
            // Sort nextLevelMap by keys to expand deterministically? 
            // "A breadth-first search that expands next states in ascending order of serialized UnitExpr satisfies this rule."
            // But we actually sort by pathKey or uStr? The spec says:
            // "The chosen conversion path must satisfy:
            // 3. Among all minimum-length paths, it is the first path in alphabetical order."
            // This is alphabetical order of the *sequence* of serialized intermediate UnitExpr.
            // i.e., `pathKey`. So if we just keep states sorted by `pathKey`, we are good.
            
            const sortedTransitions = Array.from(nextLevelMap.values()).sort((a, b) => {
                return a.state.pathKey < b.state.pathKey ? -1 : (a.state.pathKey > b.state.pathKey ? 1 : 0);
            });

            for (const t of sortedTransitions) {
                currentLevel.push(t.state);
                visited.add(t.state.uStr);
            }
        }

        throw new EvaluationError(`Error: cannot convert <${sourceStr}> to <${targetStr}>.`);
    }

    private addTransition(map: Map<string, Transition>, state: State, relTarget: string, isForward: boolean) {
        const existing = map.get(state.uStr);
        if (!existing) {
            map.set(state.uStr, { state, relTarget, isForward });
            return;
        }

        // Compare paths
        if (state.pathKey < existing.state.pathKey) {
            map.set(state.uStr, { state, relTarget, isForward });
            return;
        } else if (state.pathKey > existing.state.pathKey) {
            return;
        }

        // Same pathKey, check scales
        if (Math.abs(state.mag - existing.state.mag) > 1e-15) { // Or exact equality? Spec doesn't specify precision but exact equality is risky for floats. Let's use exact as the mathematical abstraction or check relTarget
            // "If multiple applications produce the same next UnitExpr with different numeric scales, the implementation must choose the application whose relationship target UnitId is alphabetically first."
            if (relTarget < existing.relTarget) {
                map.set(state.uStr, { state, relTarget, isForward });
                return;
            } else if (relTarget > existing.relTarget) {
                return;
            }

            if (isForward && !existing.isForward) {
                map.set(state.uStr, { state, relTarget, isForward });
            }
        }
    }
}
