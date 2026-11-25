// Renders the 27 Hebrew letters from fonts/DavidLibre-Bold.ttf with GDI+ (render-glyphs.ps1, from our
// LEGO Batman pack) in the game font's style: white fill, dark outline, 48px cell, baseline 37.
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

function renderGlyphs() {
  const out = path.join(os.tmpdir(), `tirgumim-lb2-glyphs-${process.pid}.json`);
  try {
    execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(__dirname, 'render-glyphs.ps1'),
      '-Out', out, '-FontFile', path.join(__dirname, '..', '..', 'fonts', 'DavidLibre-Bold.ttf'), '-EmSize', '46', '-Baseline', '34'],
    { stdio: 'ignore', windowsHide: true, timeout: 60000 });
    return JSON.parse(fs.readFileSync(out, 'utf8').replace(/^﻿/, '')).map((g) => {
      const px = Buffer.from(g.bgra, 'base64');
      for (let i = 0; i < px.length; i += 4) [px[i], px[i + 2]] = [px[i + 2], px[i]];
      return { code: g.code, w: g.w, h: g.h, rgba: px };
    });
  } finally {
    fs.rmSync(out, { force: true });
  }
}
module.exports = { renderGlyphs };
