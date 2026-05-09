"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DEFAULT_ABSOLUTE_TOLERANCE = exports.DEFAULT_RELATIVE_TOLERANCE = void 0;
exports.parseEvaluationLine = parseEvaluationLine;
exports.assertLinesEqual = assertLinesEqual;
exports.assertTranscript = assertTranscript;
exports.assertTranscriptCase = assertTranscriptCase;
exports.assertEvaluationLine = assertEvaluationLine;
exports.assertSingleEvaluation = assertSingleEvaluation;
exports.assertErrorLine = assertErrorLine;
exports.assertSingleError = assertSingleError;
exports.assertErrorPrefix = assertErrorPrefix;
exports.DEFAULT_RELATIVE_TOLERANCE = 1e-9;
exports.DEFAULT_ABSOLUTE_TOLERANCE = 1e-12;
const NUMBER_PATTERN = String.raw `[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?`;
const EVALUATION_LINE_PATTERN = new RegExp(String.raw `^(${NUMBER_PATTERN}) (\S+)$`);
function parseEvaluationLine(line) {
    if (typeof line !== "string") {
        throw new Error(`evaluation output line must be a string, got ${typeof line}`);
    }
    const match = EVALUATION_LINE_PATTERN.exec(line);
    if (match === null) {
        throw new Error(`expected evaluation output '<magnitude> <unit>', got ${JSON.stringify(line)}`);
    }
    const magnitudeText = match[1];
    const unit = match[2];
    if (magnitudeText === undefined || unit === undefined) {
        throw new Error(`expected evaluation output '<magnitude> <unit>', got ${JSON.stringify(line)}`);
    }
    const magnitude = Number(magnitudeText);
    if (!Number.isFinite(magnitude)) {
        throw new Error(`evaluation magnitude must be finite, got ${JSON.stringify(magnitudeText)}`);
    }
    return {
        raw: line,
        magnitudeText,
        magnitude,
        unit,
    };
}
function assertLinesEqual(actual, expected, options = {}) {
    const actualLines = coerceLines(actual, "actual");
    const expectedLines = [...expected];
    if (!sameStringArray(actualLines, expectedLines)) {
        const prefix = options.context ? `${options.context}: ` : "";
        throw new Error(`${prefix}emitted lines differ\n` +
            `expected: ${JSON.stringify(expectedLines)}\n` +
            `actual:   ${JSON.stringify(actualLines)}`);
    }
    return actualLines;
}
async function assertTranscript(runTranscript, commands, expectedOutput, options = {}) {
    const actual = await runTranscript([...commands]);
    const actualLines = await coerceLinesAsync(actual, "actual");
    return assertLinesEqual(actualLines, expectedOutput, options);
}
async function assertTranscriptCase(runTranscript, transcriptCase) {
    return assertTranscript(runTranscript, transcriptCase.commands, transcriptCase.expectedOutput, { context: transcriptCase.name });
}
function assertEvaluationLine(line, expected) {
    const parsed = parseEvaluationLine(line);
    validateTolerance(expected.tolerance?.relative ?? exports.DEFAULT_RELATIVE_TOLERANCE, "relative");
    validateTolerance(expected.tolerance?.absolute ?? exports.DEFAULT_ABSOLUTE_TOLERANCE, "absolute");
    if (!Number.isFinite(expected.magnitude)) {
        throw new Error(`expected magnitude must be finite, got ${expected.magnitude}`);
    }
    if (!magnitudesClose(parsed.magnitude, expected.magnitude, expected.tolerance)) {
        throw new Error(`magnitude differs for ${JSON.stringify(line)}: ` +
            `expected ${expected.magnitude}, got ${parsed.magnitude}`);
    }
    if (parsed.unit !== expected.unit) {
        throw new Error(`unit differs for ${JSON.stringify(line)}: ` +
            `expected ${JSON.stringify(expected.unit)}, got ${JSON.stringify(parsed.unit)}`);
    }
    return parsed;
}
function assertSingleEvaluation(lines, expected) {
    const output = coerceLines(lines, "actual");
    if (output.length !== 1) {
        throw new Error(`expected exactly one output line, got ${JSON.stringify(output)}`);
    }
    const [line] = output;
    if (line === undefined) {
        throw new Error(`expected exactly one output line, got ${JSON.stringify(output)}`);
    }
    return assertEvaluationLine(line, expected);
}
function assertErrorLine(line, expectedError) {
    if (line !== expectedError) {
        throw new Error(`expected error ${JSON.stringify(expectedError)}, got ${JSON.stringify(line)}`);
    }
}
function assertSingleError(lines, expectedError) {
    const output = coerceLines(lines, "actual");
    if (output.length !== 1) {
        throw new Error(`expected exactly one error line, got ${JSON.stringify(output)}`);
    }
    const [line] = output;
    if (line === undefined) {
        throw new Error(`expected exactly one error line, got ${JSON.stringify(output)}`);
    }
    assertErrorLine(line, expectedError);
}
function assertErrorPrefix(line) {
    if (!line.startsWith("Error:")) {
        throw new Error(`expected line to start with 'Error:', got ${JSON.stringify(line)}`);
    }
}
function magnitudesClose(actual, expected, tolerance = {}) {
    const relative = tolerance.relative ?? exports.DEFAULT_RELATIVE_TOLERANCE;
    const absolute = tolerance.absolute ?? exports.DEFAULT_ABSOLUTE_TOLERANCE;
    validateTolerance(relative, "relative");
    validateTolerance(absolute, "absolute");
    const difference = Math.abs(actual - expected);
    const scale = Math.max(Math.abs(actual), Math.abs(expected));
    return difference <= Math.max(absolute, relative * scale);
}
function validateTolerance(value, label) {
    if (!Number.isFinite(value) || value < 0) {
        throw new Error(`${label} tolerance must be finite and nonnegative, got ${value}`);
    }
}
function sameStringArray(actual, expected) {
    return (actual.length === expected.length &&
        actual.every((line, index) => line === expected[index]));
}
function coerceLines(lines, label) {
    if (typeof lines === "string") {
        throw new Error(`${label} lines must be an iterable of strings, got string`);
    }
    const coerced = [...lines];
    coerced.forEach((line, index) => {
        if (typeof line !== "string") {
            throw new Error(`${label} line ${index} must be a string, got ${typeof line}`);
        }
    });
    return coerced;
}
async function coerceLinesAsync(lines, label) {
    if (typeof lines === "string") {
        throw new Error(`${label} lines must be an iterable of strings, got string`);
    }
    if (isAsyncIterable(lines)) {
        const coerced = [];
        let index = 0;
        for await (const line of lines) {
            if (typeof line !== "string") {
                throw new Error(`${label} line ${index} must be a string, got ${typeof line}`);
            }
            coerced.push(line);
            index += 1;
        }
        return coerced;
    }
    return coerceLines(lines, label);
}
function isAsyncIterable(value) {
    const candidate = value;
    return typeof candidate[Symbol.asyncIterator] === "function";
}
