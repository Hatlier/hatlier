/**
 * Minimal QR Code generator (browser / Node, zero deps).
 * Byte mode, ECC Level L, versions 1–10, mask 0.
 * Returns a size×size matrix (1 = dark) or draws to canvas.
 *
 * Payload capacity (UTF-8 bytes): V1:17 … V10:271
 * Typical short URL → V1–V3.
 */
(function (root) {
  "use strict";

  // Byte capacity per version (ECC L)
  var CAP = [0, 17, 32, 53, 78, 106, 134, 154, 192, 230, 271];
  // Data / ECC codewords & block layout: [dataCW, ecPerBlock, nBlocks, dataPerBlock]
  // For L: blocks are equal size except V6+ where first group is shorter.
  var SPEC = [
    null,
    [19, 7, 1, 19],
    [34, 10, 1, 34],
    [55, 15, 1, 55],
    [80, 20, 1, 80],
    [108, 26, 1, 108],
    [136, 18, 2, 68],
    [156, 20, 2, 78],
    [194, 24, 2, 97],
    [232, 30, 2, 116],
    [274, 18, 4, 68],
  ];
  // Alignment pattern centers (omit 6 which is always present when list nonempty)
  var ALIGN = [
    null, [], [18], [22], [26], [30], [34],
    [22, 38], [24, 42], [26, 46], [28, 50],
  ];
  // Format bits: ECC L (01) + mask 0 (000) → BCH(15,5) = 0x77C4
  var FORMAT = 0x77c4;

  var EXP = new Uint8Array(512), LOG = new Uint8Array(256);
  (function initGF() {
    for (var i = 0, x = 1; i < 255; i++) {
      EXP[i] = x;
      LOG[x] = i;
      x <<= 1;
      if (x & 0x100) x ^= 0x11d;
    }
    for (; i < 512; i++) EXP[i] = EXP[i - 255];
  })();

  function gfMul(a, b) {
    return a && b ? EXP[LOG[a] + LOG[b]] : 0;
  }

  function rsEncode(data, ecLen) {
    var gen = [1];
    for (var i = 0; i < ecLen; i++) {
      var next = new Array(gen.length + 1).fill(0);
      for (var j = 0; j < gen.length; j++) {
        next[j] ^= gen[j]; // × (x + α^i), highest-first
        next[j + 1] ^= gfMul(gen[j], EXP[i]);
      }
      gen = next;
    }
    var msg = data.slice();
    for (i = 0; i < ecLen; i++) msg.push(0);
    for (i = 0; i < data.length; i++) {
      var f = msg[i];
      if (!f) continue;
      for (j = 0; j < gen.length; j++) msg[i + j] ^= gfMul(gen[j], f);
    }
    return msg.slice(data.length);
  }

  function bitBuf() {
    var bits = [];
    return {
      put: function (v, n) {
        for (var i = n - 1; i >= 0; i--) bits.push((v >>> i) & 1);
      },
      toBytes: function () {
        var out = [];
        for (var i = 0; i < bits.length; i += 8) {
          var b = 0;
          for (var j = 0; j < 8; j++) b = (b << 1) | (bits[i + j] || 0);
          out.push(b);
        }
        return out;
      },
      length: function () {
        return bits.length;
      },
    };
  }

  function encodeData(bytes, version) {
    var spec = SPEC[version];
    var dataCW = spec[0];
    var bb = bitBuf();
    bb.put(0b0100, 4); // byte mode
    bb.put(bytes.length, version < 10 ? 8 : 16);
    for (var i = 0; i < bytes.length; i++) bb.put(bytes[i], 8);
    // terminator
    var remain = dataCW * 8 - bb.length();
    bb.put(0, Math.min(4, remain));
    // pad to byte
    while (bb.length() % 8) bb.put(0, 1);
    var data = bb.toBytes();
    var pad = 0xec;
    while (data.length < dataCW) {
      data.push(pad);
      pad ^= 0xfd; // 0xec ↔ 0x11
    }
    return data;
  }

  function interleave(data, version) {
    var spec = SPEC[version];
    var ecLen = spec[1],
      nBlocks = spec[2],
      shortLen = Math.floor(spec[0] / nBlocks);
    var longBlocks = spec[0] % nBlocks;
    var shortBlocks = nBlocks - longBlocks;
    var blocks = [],
      ecBlocks = [],
      p = 0;
    for (var i = 0; i < nBlocks; i++) {
      var n = shortLen + (i < shortBlocks ? 0 : 1);
      var blk = data.slice(p, p + n);
      p += n;
      blocks.push(blk);
      ecBlocks.push(rsEncode(blk, ecLen));
    }
    var out = [];
    var maxD = shortLen + (longBlocks ? 1 : 0);
    for (i = 0; i < maxD; i++)
      for (var b = 0; b < nBlocks; b++) if (i < blocks[b].length) out.push(blocks[b][i]);
    for (i = 0; i < ecLen; i++) for (b = 0; b < nBlocks; b++) out.push(ecBlocks[b][i]);
    return out;
  }

  function makeMatrix(version, codewords) {
    var size = version * 4 + 17;
    var m = Array.from({ length: size }, function () {
      return new Array(size).fill(null);
    });

    function fill(r0, c0, r1, c1, v) {
      for (var r = r0; r <= r1; r++)
        for (var c = c0; c <= c1; c++) if (r >= 0 && c >= 0 && r < size && c < size) m[r][c] = v;
    }
    function finder(r, c) {
      fill(r - 1, c - 1, r + 7, c + 7, 0);
      fill(r, c, r + 6, c + 6, 1);
      fill(r + 1, c + 1, r + 5, c + 5, 0);
      fill(r + 2, c + 2, r + 4, c + 4, 1);
    }
    function alignment(r, c) {
      fill(r - 2, c - 2, r + 2, c + 2, 1);
      fill(r - 1, c - 1, r + 1, c + 1, 0);
      m[r][c] = 1;
    }

    finder(0, 0);
    finder(0, size - 7);
    finder(size - 7, 0);

    // timing
    for (var i = 8; i < size - 8; i++) {
      if (m[6][i] === null) m[6][i] = 1 - (i & 1);
      if (m[i][6] === null) m[i][6] = 1 - (i & 1);
    }

    // alignments (skip centers that fall inside finder zones; overwrite timing)
    var pos = [6].concat(ALIGN[version]);
    for (var a = 0; a < pos.length; a++)
      for (var b = 0; b < pos.length; b++) {
        var r = pos[a],
          c = pos[b];
        var inFinder =
          (r < 9 && c < 9) || (r < 9 && c > size - 10) || (r > size - 10 && c < 9);
        if (inFinder) continue;
        alignment(r, c);
      }

    // dark module
    m[size - 8][8] = 1;

    // reserve format
    for (i = 0; i < 9; i++) {
      if (m[8][i] === null) m[8][i] = 0;
      if (m[i][8] === null) m[i][8] = 0;
    }
    for (i = 0; i < 8; i++) {
      if (m[8][size - 1 - i] === null) m[8][size - 1 - i] = 0;
      if (m[size - 1 - i][8] === null) m[size - 1 - i][8] = 0;
    }

    // place data (zigzag), mask 0: (r+c)%2==0
    var bit = 0,
      total = codewords.length * 8;
    function nextBit() {
      if (bit >= total) return 0;
      var byte = codewords[bit >> 3];
      var v = (byte >> (7 - (bit & 7))) & 1;
      bit++;
      return v;
    }
    var dir = -1,
      col = size - 1;
    while (col > 0) {
      if (col === 6) col--;
      for (var row = dir < 0 ? size - 1 : 0; dir < 0 ? row >= 0 : row < size; row += dir) {
        for (var k = 0; k < 2; k++) {
          var c = col - k;
          if (m[row][c] !== null) continue;
          var v = nextBit();
          if ((row + c) % 2 === 0) v ^= 1;
          m[row][c] = v;
        }
      }
      dir = -dir;
      col -= 2;
    }

    // write format info
    function setFormat(bits) {
      // around top-left
      var map = [
        [8, 0], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5], [8, 7], [8, 8],
        [7, 8], [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8],
      ];
      for (var i = 0; i < 15; i++) {
        var bit = (bits >> (14 - i)) & 1;
        m[map[i][0]][map[i][1]] = bit;
      }
      // copy: right / bottom
      for (i = 0; i < 8; i++) m[8][size - 1 - i] = (bits >> (14 - i)) & 1;
      for (i = 0; i < 7; i++) m[size - 7 + i][8] = (bits >> (6 - i)) & 1;
    }
    setFormat(FORMAT);

    // null → 0
    for (var r = 0; r < size; r++)
      for (var c = 0; c < size; c++) if (m[r][c] === null) m[r][c] = 0;
    return m;
  }

  function toBytes(text) {
    if (typeof TextEncoder !== "undefined") return Array.from(new TextEncoder().encode(text));
    var out = [];
    for (var i = 0; i < text.length; i++) {
      var c = text.charCodeAt(i);
      if (c < 0x80) out.push(c);
      else if (c < 0x800) out.push(0xc0 | (c >> 6), 0x80 | (c & 63));
      else out.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    }
    return out;
  }

  function qrMatrix(text) {
    var bytes = typeof text === "string" ? toBytes(text) : Array.from(text);
    var version = 1;
    while (version <= 10 && bytes.length > CAP[version]) version++;
    if (version > 10) throw new Error("Data too long for QR versions 1–10 (ECC L)");
    var data = encodeData(bytes, version);
    var codewords = interleave(data, version);
    var modules = makeMatrix(version, codewords);
    return { version: version, size: modules.length, modules: modules };
  }

  function qrDraw(canvas, text, opt) {
    opt = opt || {};
    var scale = opt.scale || 6;
    var margin = opt.margin != null ? opt.margin : 4;
    var dark = opt.dark || "#000";
    var light = opt.light || "#fff";
    var q = qrMatrix(text);
    var n = q.size;
    var ctx = canvas.getContext("2d");
    canvas.width = canvas.height = (n + margin * 2) * scale;
    ctx.fillStyle = light;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = dark;
    for (var y = 0; y < n; y++)
      for (var x = 0; x < n; x++)
        if (q.modules[y][x])
          ctx.fillRect((x + margin) * scale, (y + margin) * scale, scale, scale);
    return q;
  }

  root.qrMatrix = qrMatrix;
  root.qrDraw = qrDraw;
})(typeof self !== "undefined" ? self : globalThis);
