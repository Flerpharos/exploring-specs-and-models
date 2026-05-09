const NUMBER_RE = /^(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?/;
const UNIT_ID_RE = /^[a-z][a-z_]*/;
const VAR_ID_RE = /^[A-Z][A-Z_]*/;
const OP_RE = /^[+\-*/^()[\]]/;
const WS_RE = /^\s+/;

function tokenize(text: string) {
    let i = 0;
    while (i < text.length) {
        const s = text.slice(i);
        let m;
        if ((m = s.match(WS_RE))) { i += m[0].length; continue; }
        if ((m = s.match(NUMBER_RE))) { console.log('NUM', m[0]); i += m[0].length; continue; }
        if ((m = s.match(UNIT_ID_RE))) { console.log('UNIT', m[0]); i += m[0].length; continue; }
        if ((m = s.match(VAR_ID_RE))) { console.log('VAR', m[0]); i += m[0].length; continue; }
        if ((m = s.match(OP_RE))) { console.log('OP', m[0]); i += m[0].length; continue; }
        console.log('ERR', s[0]);
        i++;
    }
}
tokenize("1 m/s + X * (2.5e-3) [ ]");
