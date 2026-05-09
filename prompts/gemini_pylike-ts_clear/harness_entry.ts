import { Environment } from "./environment";
import { executeCommand } from "./cli";

export const runTranscript = async (commands: string[]): Promise<string[]> => {
    const env = new Environment();
    const output: string[] = [];

    for (const line of commands) {
        const res = executeCommand(line, env);
        if (res !== null) {
            output.push(res);
        }
    }

    return output;
};
