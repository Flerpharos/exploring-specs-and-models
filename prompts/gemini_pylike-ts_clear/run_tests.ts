import { runTranscript } from './harness_entry';
import { assertTranscriptCase } from './unitFormulaHarness';

async function test() {
    try {
        await assertTranscriptCase(runTranscript, {
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
    } catch (e) {
        console.error(e);
    }
}

test();
