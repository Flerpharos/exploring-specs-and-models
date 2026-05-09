"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const harness_entry_1 = require("./harness_entry");
const unitFormulaHarness_1 = require("./unitFormulaHarness");
async function test() {
    try {
        await (0, unitFormulaHarness_1.assertTranscriptCase)(harness_entry_1.runTranscript, {
            name: "Basic Unit & Set",
            commands: [
                "unit:m",
                "unit:s",
                "set:X:2 m",
                "evaluate:X:m"
            ],
            expectedOutput: [
                "2 m"
            ]
        });
        console.log("Basic passed.");
    }
    catch (e) {
        console.error(e);
    }
}
test();
