# LEGO Batman 2: DC Super Heroes, first look (2026-11-26)

- Steam 213330, `D:\SteamLibrary\steamapps\common\LEGO Batman 2`, `LEGOBatman2.exe` (TT engine, 2012).
  Archives GAME.DAT, GAME0/1/2.DAT: TT .DAT index version -4 ("PakDat v1.01"), same 16-byte entries and name
  tree as LEGO Batman (2008) (`tools/ttdat.py`, port of our lego-batman ttdat.js). Flags low byte 0 = stored.
- Text (all stored uncompressed in GAME.DAT):
  - `stuff/text/text.csv`: columns LABEL, PLATFORM, TYPE, ENGLISH, AMERICAN, ... 1,532 rows, ~10.8k words
    (types Subtitle 424, LegoAPI 326, Char 184, Hint 141, TRC 138, Game 124...; platforms All/PC/X360/Wii/PS3).
  - 117 cutscene CSVs `cut/story/<level>/<scene>.csv` (same columns, "Speaker: line" subtitles).
  - `stuff/text/english_credits.txt`, `american_credits.txt`, `levels/credits/credits.txt` (GAME0.DAT).
- Font `gui/font/font_nxg.ft2` (big-endian): u32 3026 (header size), u32 1, 'TNFN'(=NFNT), u32 3, ...,
  u32 184 glyphs, u32 186 map entries, f32 48 (line height?), 37, 12; 'ROTV' + count + glyphs (f32 x, y, width);
  'ROTV' + count + map (u16 codepoint, u16 glyph); 'ROTV' 0 (kerning?); then a DDS DXT5 atlas.
  Plan like LEGO Batman 1: reuse slots of accented letters for the 27 Hebrew letters, draw them into the atlas.
- RTL: engine draws left to right: visual order + pre-wrap (port lego-batman rtl.js).
- Activation: as lego-batman (proxy XINPUT/other DLL, GAME.DAT append copy + index overlay). Check imports.
- Odd extra files in the install (rldata.dll, dfe, *.nfs, *.fbrb, *.sub, *.bix, keyMenu4Pt_v2.cf): not ours,
  leave them alone.
