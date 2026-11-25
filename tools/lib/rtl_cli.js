// stdin: {"maxWidth": N, "lineBreak": "\n" | "\\n", "strings": {id: logical Hebrew}}
// stdout: {id: visual-order text} (rtl.js from our LEGO Batman pack).
const rtl = require('./rtl');
let input = '';
process.stdin.on('data', (d) => (input += d));
process.stdin.on('end', () => {
  const { maxWidth, lineBreak, strings } = JSON.parse(input);
  const out = {};
  for (const [id, s] of Object.entries(strings)) {
    let v = rtl.toVisual(s, { maxWidth });
    if (lineBreak !== rtl.LINE_BREAK) v = v.split(rtl.LINE_BREAK).join(lineBreak);
    out[id] = v;
  }
  process.stdout.write(JSON.stringify(out));
});
