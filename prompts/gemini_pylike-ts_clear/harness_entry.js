"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.runTranscript = void 0;
const environment_1 = require("./environment");
const cli_1 = require("./cli");
const runTranscript = async (commands) => {
    const env = new environment_1.Environment();
    const output = [];
    for (const line of commands) {
        const res = (0, cli_1.executeCommand)(line, env);
        if (res !== null) {
            output.push(res);
        }
    }
    return output;
};
exports.runTranscript = runTranscript;
