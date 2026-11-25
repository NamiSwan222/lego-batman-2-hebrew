// Adds Hebrew letters to LEGO Batman 2's font (gui/font/font_nxg.ft2) without changing its size: accented
// Latin glyphs the Hebrew text doesn't use give up their glyph slots and atlas space, and the Hebrew letters
// are painted into the DXT5 atlas. Same method as our LEGO Batman (2008) font.js; only the file layout differs.
//
// .ft2 layout (big-endian; worked out from the game's file):
//   0x00 u32  DDS offset - 4          0x08 'TNFN'   0x0c u32 version (3)
//   0x18 u16  ?   0x1a u32 glyph count (n)   0x1e u32 map count
//   0x22 f32  cell height (48)   0x26 f32 baseline (37)   0x2a f32 12
//   then 'ROTV' u32 n, n x { f32 x, f32 y, f32 width }
//        'ROTV' u32 count, count x { u16 codepoint, u16 glyph } sorted by codepoint
//        'ROTV' u32 0
//   DDS (little-endian, DXT5) atlas with mips
const dxt5 = require('./dxt5');

const HEBREW = Array.from({ length: 27 }, (_, i) => 0x05d0 + i);

function parse(buf) {
  if (buf.toString('latin1', 8, 12) !== 'TNFN') throw new Error('ft2: not a TT NFNT font');
  const n = buf.readUInt32BE(0x1a);
  const mcount = buf.readUInt32BE(0x1e);
  const t1 = buf.indexOf('ROTV', 0x20, 'latin1');
  if (buf.readUInt32BE(t1 + 4) !== n) throw new Error('ft2: glyph table count mismatch');
  const recOff = t1 + 8;
  const t2 = recOff + n * 12;
  if (buf.toString('latin1', t2, t2 + 4) !== 'ROTV' || buf.readUInt32BE(t2 + 4) !== mcount) throw new Error('ft2: map table not found');
  const mapOff = t2 + 8;
  const map = [];
  const tail = [];  // the list ends with a 0xFFFF terminator entry; kept as is
  for (let i = 0; i < mcount; i++) {
    const e = { code: buf.readUInt16BE(mapOff + i * 4), glyph: buf.readUInt16BE(mapOff + i * 4 + 2) };
    (e.code === 0xffff ? tail : map).push(e);
  }
  const dds = buf.readUInt32BE(0) + 4;
  if (buf.toString('latin1', dds, dds + 4) !== 'DDS ') throw new Error('ft2: DDS header not found');
  if (buf.toString('latin1', dds + 84, dds + 88) !== 'DXT5') throw new Error('ft2: atlas is not DXT5');
  return {
    n, recOff, mapOff, map, tail, dds,
    cellHeight: buf.readFloatBE(0x22),
    height: buf.readUInt32LE(dds + 12),
    width: buf.readUInt32LE(dds + 16),
    mips: Math.max(1, buf.readUInt32LE(dds + 28)),
    record(g) {
      const o = recOff + g * 12;
      return { x: buf.readFloatBE(o), y: buf.readFloatBE(o + 4), w: buf.readFloatBE(o + 8) };
    },
  };
}

function isRemovable(code) {
  if (code >= 0xc0 && code <= 0x17f) return true; // accented Latin letters
  return 'œ¡¿ªº²'.includes(String.fromCharCode(code));
}

function baseLetter(code) {
  const base = String.fromCharCode(code).normalize('NFD').replace(/[̀-ͯ]/g, '');
  return base.length === 1 ? base.charCodeAt(0) : null;
}

/** ft2: original font Buffer; glyphs: [{ code, w, h, rgba }]; usedChars: Set of code points the text uses. */
function addGlyphs(ft2, glyphs, usedChars) {
  const out = Buffer.from(ft2);
  const f = parse(out);
  const W = f.width;
  const H = f.height;
  const removed = f.map.filter((m) => isRemovable(m.code) && !usedChars.has(m.code));
  const kept = f.map.filter((m) => !removed.includes(m));
  const keptGlyphs = new Set(kept.map((m) => m.glyph));
  const freeSlots = [...new Set(removed.map((m) => m.glyph))].filter((g) => !keptGlyphs.has(g));
  if (freeSlots.length < glyphs.length || removed.length < glyphs.length) {
    throw new Error(`ft2: only ${freeSlots.length} free glyph slots for ${glyphs.length} new letters`);
  }
  const level0 = dxt5.decode(out, f.dds + 128, W, H);
  const occupied = new Uint8Array(W * H);
  const mark = (r, val) => {
    for (let y = Math.max(0, Math.floor(r.y)); y < Math.min(H, Math.ceil(r.y + f.cellHeight)); y++) {
      for (let x = Math.max(0, Math.floor(r.x) - 1); x < Math.min(W, Math.ceil(r.x + r.w) + 1); x++) occupied[y * W + x] = val;
    }
  };
  for (const g of keptGlyphs) {
    const r = f.record(g);
    if (r.w > 0) mark(r, 1);
  }
  const original = Buffer.from(level0);
  for (let i = 0; i < W * H; i++) if (!occupied[i]) level0.writeUInt32LE(0, i * 4);
  const bands = [...new Set(f.map.map((m) => f.record(m.glyph).y))].filter((y) => y >= 0 && y + f.cellHeight <= H).sort((a, b) => a - b);
  const fits = (x, y, w) => {
    for (let yy = y; yy < y + f.cellHeight; yy++) for (let xx = x; xx < x + w; xx++) if (occupied[yy * W + xx]) return false;
    return true;
  };
  const placed = [];
  for (const [i, gl] of glyphs.entries()) {
    let spot = null;
    for (const y of bands) {
      for (let x = 2; x + gl.w <= W - 2 && !spot; x++) if (fits(x, y, gl.w)) spot = { x, y };
      if (spot) break;
    }
    if (!spot) throw new Error(`ft2: no room in the atlas for U+${gl.code.toString(16)}`);
    for (let yy = 0; yy < gl.h && spot.y + yy < H; yy++) {
      for (let xx = 0; xx < gl.w; xx++) {
        const s = (yy * gl.w + xx) * 4;
        gl.rgba.copy(level0, ((spot.y + yy) * W + spot.x + xx) * 4, s, s + 4);
      }
    }
    const rec = { x: spot.x, y: spot.y, w: gl.w };
    mark(rec, 1);
    const o = f.recOff + freeSlots[i] * 12;
    out.writeFloatBE(rec.x, o);
    out.writeFloatBE(rec.y, o + 4);
    out.writeFloatBE(rec.w, o + 8);
    placed.push({ code: gl.code, glyph: freeSlots[i] });
  }
  const byCode = new Map(kept.map((m) => [m.code, m.glyph]));
  const spare = removed.slice(placed.length).map((m) => ({ code: m.code, glyph: byCode.get(baseLetter(m.code)) ?? byCode.get(32) ?? 0 }));
  const entries = [...kept, ...placed, ...spare].map((e) => ({ code: e.code, glyph: e.glyph })).sort((a, b) => a.code - b.code).concat(f.tail);
  entries.forEach((e, i) => {
    out.writeUInt16BE(e.code, f.mapOff + i * 4);
    out.writeUInt16BE(e.glyph, f.mapOff + i * 4 + 2);
  });
  // re-encode the DXT blocks (all mips) whose level-0 pixels changed
  const bw0 = Math.ceil(W / 4);
  const changed = new Uint8Array(bw0 * Math.ceil(H / 4));
  for (let i = 0; i < W * H; i++) {
    if (original.readUInt32LE(i * 4) !== level0.readUInt32LE(i * 4)) changed[Math.floor(Math.floor(i / W) / 4) * bw0 + Math.floor((i % W) / 4)] = 1;
  }
  const touchedAt = (level, bx, by) => {
    const s = 1 << level;
    for (let y = by * s; y < Math.min((by + 1) * s, H / 4); y++) for (let x = bx * s; x < Math.min((bx + 1) * s, bw0); x++) if (changed[y * bw0 + x]) return true;
    return false;
  };
  let img = level0;
  let w = W;
  let h = H;
  let off = f.dds + 128;
  for (let level = 0; level < f.mips; level++) {
    const bw = Math.max(1, Math.ceil(w / 4));
    const bh = Math.max(1, Math.ceil(h / 4));
    for (let by = 0; by < bh; by++) for (let bx = 0; bx < bw; bx++) if (touchedAt(level, bx, by)) dxt5.encodeBlock(img, w, h, bx, by).copy(out, off + (by * bw + bx) * 16);
    off += bw * bh * 16;
    if (w === 1 && h === 1) break;
    img = dxt5.downsample(img, w, h);
    w = Math.max(1, w >> 1);
    h = Math.max(1, h >> 1);
  }
  return out;
}

module.exports = { parse, addGlyphs, HEBREW };
