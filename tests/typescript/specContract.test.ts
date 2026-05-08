export type RunResult = string | null | undefined;
export interface UnitCliAdapter { run(command: string): RunResult; }
declare const describe: (name: string, fn: () => void) => void;
declare const test: (name: string, fn: () => void) => void;
declare const beforeEach: (fn: () => void) => void;
declare const expect: (value: unknown) => { toBe: (expected: unknown) => void; toBeGreaterThan: (n: number) => void; toBeLessThanOrEqual: (n: number) => void; };
const ok = (v: RunResult) => expect(v ?? "").toBe("");

function expectValue(v: RunResult, magnitude: number, unit: string, cmd: string): void {
  expect(typeof v).toBe("string");
  const s = v as string;
  const i = s.lastIndexOf(" ");
  expect(i).toBeGreaterThan(0);
  const gotMag = Number.parseFloat(s.slice(0, i));
  const gotUnit = s.slice(i + 1);
  expect(Number.isFinite(gotMag)).toBe(true);
  expect(gotUnit).toBe(unit);
  expect(Math.abs(gotMag - magnitude)).toBeLessThanOrEqual(1e-12);
}

export function defineUnitAwareSpecContractTests(name: string, createAdapter: () => UnitCliAdapter): void {
  describe(name, () => {
    let cli: UnitCliAdapter;
    const err = (cmd: string, expected: string) => expect(cli.run(cmd)).toBe(expected);
    const value = (cmd: string, magnitude: number, unit: string) => expectValue(cli.run(cmd), magnitude, unit, cmd);
    beforeEach(() => { cli = createAdapter(); });

    test("identifier and command syntax", () => {
      err("unit:M", "Error: invalid unit name.");
      err("unit:m2", "Error: invalid unit name.");
      ok(cli.run("unit:meters_per_second"));
      err("set:x:1", "Error: invalid variable name.");
      err("set:X2:1", "Error: invalid variable name.");
      err("set:X", "Error: invalid command syntax.");
      err("evaluate:", "Error: invalid command syntax.");
      err("noop:1", "Error: unknown command.");
    });

    test("value literals and unit section", () => {
      ok(cli.run("unit:m")); ok(cli.run("unit:s")); ok(cli.run("unit:kg"));
      value("evaluate:2+3", 5, "1");
      value("evaluate:2 m/s", 2, "m/s");
      value("evaluate:3 (m/s)^2", 3, "m^2/s^2");
      value("evaluate:4 kg*m/s^2", 4, "kg*m/s^2");
      value("evaluate:3 1/s", 3, "1/s");
      err("evaluate:2 m x", "Error: invalid formula.");
    });

    test("value context resolution", () => {
      ok(cli.run("unit:m"));
      ok(cli.run("set:X:3 m"));
      value("evaluate:X", 3, "m");
      err("evaluate:Y", "Error: unknown variable Y.");
      value("evaluate:m", 1, "m");
      err("evaluate:s", "Error: unknown unit s.");
    });

    test("operator precedence and errors", () => {
      value("evaluate:-2^2", 4, "1");
      value("evaluate:-(2^2)", -4, "1");
      value("evaluate:2^3^2", 512, "1");
      value("evaluate:8/2*3", 12, "1");
      value("evaluate:]0", 1, "1");
      value("evaluate:[ ]1", 1, "1");
      err("evaluate:1/0", "Error: division by zero.");
      ok(cli.run("unit:m"));
      err("evaluate:2^1 m", "Error: exponent must be scalar.");
      err("evaluate:[2 m", "Error: log argument must be scalar.");
      err("evaluate:[0", "Error: log argument must be positive.");
      err("evaluate:]1 m", "Error: exp argument must be scalar.");
    });

    test("add/sub unit unification", () => {
      ok(cli.run("unit:m")); ok(cli.run("unit:cm"));
      ok(cli.run("relate:cm:m:0.01 m"));
      value("evaluate:1 m + 50 cm", 1.5, "m");
      value("evaluate:1 m - 50 cm", 0.5, "m");
      ok(cli.run("unit:s"));
      err("evaluate:1 m + 1 s", "Error: cannot convert s to m.");
    });

    test("relate source list and context rules", () => {
      ok(cli.run("unit:m")); ok(cli.run("unit:cm")); ok(cli.run("unit:s"));
      err("relate:cm:m,m:1 m", "Error: invalid unit list.");
      err("relate:cm:cm:1 cm", "Error: invalid unit list.");
      err("relate:cm:s:1 s", "Error: invalid unit list.");
      err("relate:cm:m:m+m", "Error: invalid formula.");
      err("relate:cm:m:[m", "Error: invalid formula.");
      err("relate:cm:m:1 s", "Error: unknown unit s.");
      ok(cli.run("set:Z:7"));
      err("relate:cm:m:Z", "Error: unknown unit Z.");
    });

    test("relate replaces existing", () => {
      ok(cli.run("unit:m")); ok(cli.run("unit:cm"));
      ok(cli.run("relate:cm:m:0.01 m"));
      ok(cli.run("relate:cm:m:0.02 m"));
      value("evaluate:1 m:cm", 50, "cm");
    });

    test("output unit context and precedence", () => {
      ok(cli.run("unit:m"));
      err("evaluate:UNKNOWN_VAR:m/)", "Error: invalid output unit.");
      err("evaluate:1/0:m/)", "Error: invalid output unit.");
      err("evaluate:1 m:s", "Error: unknown unit s.");
      err("evaluate:1 m:", "Error: invalid command syntax.");
      err("evaluate:1 m:2 m", "Error: invalid output unit.");
    });

    test("conversion and shortest path", () => {
      ok(cli.run("unit:m")); ok(cli.run("unit:cm")); ok(cli.run("unit:s"));
      ok(cli.run("relate:cm:m:0.01 m"));
      value("evaluate:1 m:cm", 100, "cm");
      value("evaluate:1 cm:m", 0.01, "m");
      err("evaluate:1 m:s", "Error: cannot convert m to s.");
      ok(cli.run("relate:m:cm:101 cm"));
      value("evaluate:1 m:cm", 100, "cm");
    });

    test("conversion applies to powers", () => {
      ok(cli.run("unit:m")); ok(cli.run("unit:cm"));
      ok(cli.run("relate:cm:m:0.01 m"));
      value("evaluate:1 m^2:cm^2", 10000, "cm^2");
      value("evaluate:1/cm:m^-1", 100, "m^-1");
    });

    test("relationship invalid factor", () => {
      ok(cli.run("unit:m"));
      err("relate:cm:m:0 m", "Error: invalid relationship.");
    });

    test("evaluate parsing uses last colon split", () => {
      ok(cli.run("unit:m"));
      value("evaluate:1 m:m", 1, "m");
    });

    test("failed commands do not mutate", () => {
      ok(cli.run("set:X:3"));
      err("set:X:1/0", "Error: division by zero.");
      value("evaluate:X", 3, "1");
    });
  });
}
