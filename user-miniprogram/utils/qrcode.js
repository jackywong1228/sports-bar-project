/**
 * QR Code Generator for WeChat Mini Program
 * Lightweight, zero-dependency QR code generation with canvas 2D API support.
 * Supports alphanumeric and UTF-8 byte mode encoding.
 */

// ---------- GF(256) arithmetic ----------
const EXP_TABLE = new Array(256)
const LOG_TABLE = new Array(256)
;(function initGaloisField() {
  let x = 1
  for (let i = 0; i < 256; i++) {
    EXP_TABLE[i] = x
    LOG_TABLE[x] = i
    x <<= 1
    if (x & 0x100) x ^= 0x11d
  }
})()

function gfMul(a, b) {
  if (a === 0 || b === 0) return 0
  return EXP_TABLE[(LOG_TABLE[a] + LOG_TABLE[b]) % 255]
}

// ---------- Reed-Solomon error correction ----------
function rsGenPoly(nsym) {
  let g = [1]
  for (let i = 0; i < nsym; i++) {
    const ng = new Array(g.length + 1).fill(0)
    for (let j = 0; j < g.length; j++) {
      ng[j] ^= g[j]
      ng[j + 1] ^= gfMul(g[j], EXP_TABLE[i])
    }
    g = ng
  }
  return g
}

function rsEncode(data, nsym) {
  const gen = rsGenPoly(nsym)
  const res = new Array(data.length + nsym).fill(0)
  for (let i = 0; i < data.length; i++) res[i] = data[i]
  for (let i = 0; i < data.length; i++) {
    const coef = res[i]
    if (coef !== 0) {
      for (let j = 0; j < gen.length; j++) {
        res[i + j] ^= gfMul(gen[j], coef)
      }
    }
  }
  return res.slice(data.length)
}

// ---------- QR code version / capacity tables ----------
// [total codewords, ec codewords per block, num blocks group1, data cw group1, num blocks group2, data cw group2]
// We support versions 1-10 with error correction level M
const VERSION_TABLE = {
  1:  [26,  10, 1, 16, 0, 0],
  2:  [44,  16, 1, 28, 0, 0],
  3:  [70,  26, 1, 44, 0, 0],
  4:  [100, 18, 2, 32, 0, 0],
  5:  [134, 24, 2, 43, 0, 0],
  6:  [172, 16, 4, 27, 0, 0],
  7:  [196, 18, 4, 31, 0, 0],
  8:  [242, 22, 2, 38, 2, 39],
  9:  [292, 22, 3, 36, 2, 37],
  10: [346, 26, 4, 43, 1, 44],
}

// Byte mode capacity for EC level M, versions 1-10
const BYTE_CAPACITY = [0, 14, 26, 42, 62, 84, 106, 122, 152, 180, 213]

// Alignment pattern positions per version
const ALIGN_POS = {
  2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
  6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]
}

// Format info bits for EC level M, masks 0-7
const FORMAT_INFO = [
  0x5412, 0x5125, 0x5E7C, 0x5B4B, 0x45F9, 0x40CE, 0x4F97, 0x4AA0
]

// Version info bits for versions 7-10
const VERSION_INFO = {
  7: 0x07C94, 8: 0x085BC, 9: 0x09A99, 10: 0x0A4D3
}

// ---------- Data encoding (byte mode) ----------
function encodeData(text) {
  const bytes = []
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i)
    if (code < 0x80) {
      bytes.push(code)
    } else if (code < 0x800) {
      bytes.push(0xc0 | (code >> 6), 0x80 | (code & 0x3f))
    } else if (code >= 0xD800 && code <= 0xDBFF) {
      // surrogate pair
      const hi = code, lo = text.charCodeAt(++i)
      const cp = ((hi - 0xD800) << 10) + (lo - 0xDC00) + 0x10000
      bytes.push(0xf0 | (cp >> 18), 0x80 | ((cp >> 12) & 0x3f), 0x80 | ((cp >> 6) & 0x3f), 0x80 | (cp & 0x3f))
    } else {
      bytes.push(0xe0 | (code >> 12), 0x80 | ((code >> 6) & 0x3f), 0x80 | (code & 0x3f))
    }
  }
  return bytes
}

function selectVersion(dataLen) {
  for (let v = 1; v <= 10; v++) {
    if (dataLen <= BYTE_CAPACITY[v]) return v
  }
  throw new Error('Data too long for QR code (max ~213 bytes at version 10)')
}

function buildDataCodewords(bytes, version) {
  const info = VERSION_TABLE[version]
  const totalDataCW = info[2] * info[3] + info[4] * info[5]
  const charCountBits = version <= 9 ? 8 : 16

  // Build bit stream
  const bits = []
  function pushBits(val, len) {
    for (let i = len - 1; i >= 0; i--) bits.push((val >> i) & 1)
  }

  pushBits(0b0100, 4) // byte mode indicator
  pushBits(bytes.length, charCountBits)
  for (const b of bytes) pushBits(b, 8)

  // Terminator
  const maxBits = totalDataCW * 8
  const termLen = Math.min(4, maxBits - bits.length)
  pushBits(0, termLen)

  // Pad to byte boundary
  while (bits.length % 8 !== 0) bits.push(0)

  // Pad codewords
  const padBytes = [0xEC, 0x11]
  let pi = 0
  while (bits.length < maxBits) {
    pushBits(padBytes[pi], 8)
    pi = (pi + 1) % 2
  }

  // Convert to codewords
  const codewords = []
  for (let i = 0; i < bits.length; i += 8) {
    let val = 0
    for (let j = 0; j < 8; j++) val = (val << 1) | bits[i + j]
    codewords.push(val)
  }
  return codewords
}

// ---------- Block interleaving + EC ----------
function interleave(dataCW, version) {
  const info = VERSION_TABLE[version]
  const ecCWPerBlock = info[1]
  const g1Blocks = info[2], g1DataCW = info[3]
  const g2Blocks = info[4], g2DataCW = info[5]

  const blocks = []
  let offset = 0
  for (let i = 0; i < g1Blocks; i++) {
    blocks.push(dataCW.slice(offset, offset + g1DataCW))
    offset += g1DataCW
  }
  for (let i = 0; i < g2Blocks; i++) {
    blocks.push(dataCW.slice(offset, offset + g2DataCW))
    offset += g2DataCW
  }

  const ecBlocks = blocks.map(b => rsEncode(b, ecCWPerBlock))

  // Interleave data
  const result = []
  const maxDataLen = Math.max(g1DataCW, g2DataCW)
  for (let i = 0; i < maxDataLen; i++) {
    for (const b of blocks) {
      if (i < b.length) result.push(b[i])
    }
  }
  // Interleave EC
  for (let i = 0; i < ecCWPerBlock; i++) {
    for (const ec of ecBlocks) {
      result.push(ec[i])
    }
  }
  return result
}

// ---------- Module placement ----------
function createMatrix(version) {
  const size = version * 4 + 17
  const matrix = Array.from({ length: size }, () => new Array(size).fill(-1))
  const reserved = Array.from({ length: size }, () => new Array(size).fill(false))
  return { matrix, reserved, size }
}

function placeFinder(matrix, reserved, row, col) {
  for (let r = -1; r <= 7; r++) {
    for (let c = -1; c <= 7; c++) {
      const rr = row + r, cc = col + c
      if (rr < 0 || rr >= matrix.length || cc < 0 || cc >= matrix.length) continue
      let val = 0
      if (r >= 0 && r <= 6 && c >= 0 && c <= 6) {
        if (r === 0 || r === 6 || c === 0 || c === 6 || (r >= 2 && r <= 4 && c >= 2 && c <= 4)) {
          val = 1
        }
      }
      matrix[rr][cc] = val
      reserved[rr][cc] = true
    }
  }
}

function placeAlignment(matrix, reserved, version) {
  if (!ALIGN_POS[version]) return
  const positions = ALIGN_POS[version]
  for (const r of positions) {
    for (const c of positions) {
      if (reserved[r][c]) continue
      for (let dr = -2; dr <= 2; dr++) {
        for (let dc = -2; dc <= 2; dc++) {
          const val = (Math.abs(dr) === 2 || Math.abs(dc) === 2 || (dr === 0 && dc === 0)) ? 1 : 0
          matrix[r + dr][c + dc] = val
          reserved[r + dr][c + dc] = true
        }
      }
    }
  }
}

function placeTiming(matrix, reserved, size) {
  for (let i = 8; i < size - 8; i++) {
    const val = i % 2 === 0 ? 1 : 0
    if (!reserved[6][i]) { matrix[6][i] = val; reserved[6][i] = true }
    if (!reserved[i][6]) { matrix[i][6] = val; reserved[i][6] = true }
  }
}

function reserveFormatAndVersion(matrix, reserved, size, version) {
  // Format info areas
  for (let i = 0; i <= 8; i++) {
    if (i < size) { reserved[8][i] = true; reserved[i][8] = true }
  }
  for (let i = 0; i < 7; i++) {
    reserved[size - 1 - i][8] = true
  }
  for (let i = 0; i < 8; i++) {
    reserved[8][size - 8 + i] = true
  }
  // Dark module
  matrix[size - 8][8] = 1
  reserved[size - 8][8] = true

  // Version info areas (versions 7+)
  if (version >= 7) {
    for (let i = 0; i < 6; i++) {
      for (let j = 0; j < 3; j++) {
        reserved[i][size - 11 + j] = true
        reserved[size - 11 + j][i] = true
      }
    }
  }
}

function placeData(matrix, reserved, size, bits) {
  let bitIdx = 0
  let upward = true
  for (let col = size - 1; col >= 0; col -= 2) {
    if (col === 6) col = 5 // skip timing column
    const rows = upward ? Array.from({ length: size }, (_, i) => size - 1 - i) : Array.from({ length: size }, (_, i) => i)
    for (const row of rows) {
      for (let dc = 0; dc >= -1; dc--) {
        const c = col + dc
        if (c < 0 || reserved[row][c]) continue
        matrix[row][c] = bitIdx < bits.length ? bits[bitIdx++] : 0
      }
    }
    upward = !upward
  }
}

// ---------- Masking ----------
const MASK_FNS = [
  (r, c) => (r + c) % 2 === 0,
  (r, c) => r % 2 === 0,
  (r, c) => c % 3 === 0,
  (r, c) => (r + c) % 3 === 0,
  (r, c) => (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0,
  (r, c) => ((r * c) % 2) + ((r * c) % 3) === 0,
  (r, c) => (((r * c) % 2) + ((r * c) % 3)) % 2 === 0,
  (r, c) => (((r + c) % 2) + ((r * c) % 3)) % 2 === 0,
]

function applyMask(matrix, reserved, size, maskIdx) {
  const fn = MASK_FNS[maskIdx]
  const result = matrix.map(row => [...row])
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (!reserved[r][c] && fn(r, c)) {
        result[r][c] ^= 1
      }
    }
  }
  return result
}

function placeFormatInfo(matrix, size, maskIdx) {
  const formatBits = FORMAT_INFO[maskIdx]
  // First copy (around top-left finder)
  // Horizontal: row=8, cols 0,1,2,3,4,5,7,8 → bits 14..7
  const hCols = [0, 1, 2, 3, 4, 5, 7, 8]
  for (let i = 0; i < 8; i++) {
    matrix[8][hCols[i]] = (formatBits >> (14 - i)) & 1
  }
  // Vertical: col=8, rows 0,1,2,3,4,5,7,8 → bits 14..7
  const vRows = [0, 1, 2, 3, 4, 5, 7, 8]
  for (let i = 0; i < 8; i++) {
    matrix[vRows[i]][8] = (formatBits >> (14 - i)) & 1
  }
  // Second copy (around top-right + bottom-left finders)
  // Horizontal: row=8, cols size-8..size-1 → bits 7..0
  for (let i = 0; i < 8; i++) {
    matrix[8][size - 8 + i] = (formatBits >> (7 - i)) & 1
  }
  // Vertical: col=8, rows size-7..size-1 → bits 6..0
  for (let i = 0; i < 7; i++) {
    matrix[size - 7 + i][8] = (formatBits >> (6 - i)) & 1
  }
}

function placeVersionInfo(matrix, size, version) {
  if (version < 7) return
  const vInfo = VERSION_INFO[version]
  for (let i = 0; i < 6; i++) {
    for (let j = 0; j < 3; j++) {
      const bit = (vInfo >> (i * 3 + j)) & 1
      matrix[i][size - 11 + j] = bit
      matrix[size - 11 + j][i] = bit
    }
  }
}

// Penalty score calculation for mask selection
function penaltyScore(matrix, size) {
  let score = 0

  // Rule 1: runs of same color in row/col
  for (let r = 0; r < size; r++) {
    let count = 1
    for (let c = 1; c < size; c++) {
      if (matrix[r][c] === matrix[r][c - 1]) { count++ }
      else { if (count >= 5) score += count - 2; count = 1 }
    }
    if (count >= 5) score += count - 2
  }
  for (let c = 0; c < size; c++) {
    let count = 1
    for (let r = 1; r < size; r++) {
      if (matrix[r][c] === matrix[r - 1][c]) { count++ }
      else { if (count >= 5) score += count - 2; count = 1 }
    }
    if (count >= 5) score += count - 2
  }

  // Rule 2: 2x2 blocks
  for (let r = 0; r < size - 1; r++) {
    for (let c = 0; c < size - 1; c++) {
      const v = matrix[r][c]
      if (v === matrix[r][c + 1] && v === matrix[r + 1][c] && v === matrix[r + 1][c + 1]) {
        score += 3
      }
    }
  }

  // Rule 3: finder-like patterns (1,0,1,1,1,0,1,0,0,0,0 or reverse) → +40 each
  const finderA = [1,0,1,1,1,0,1,0,0,0,0]
  const finderB = [0,0,0,0,1,0,1,1,1,0,1]
  for (let r = 0; r < size; r++) {
    for (let c = 0; c <= size - 11; c++) {
      let matchA = true, matchB = true
      for (let k = 0; k < 11; k++) {
        if (matrix[r][c + k] !== finderA[k]) matchA = false
        if (matrix[r][c + k] !== finderB[k]) matchB = false
        if (!matchA && !matchB) break
      }
      if (matchA) score += 40
      if (matchB) score += 40
    }
  }
  for (let c = 0; c < size; c++) {
    for (let r = 0; r <= size - 11; r++) {
      let matchA = true, matchB = true
      for (let k = 0; k < 11; k++) {
        if (matrix[r + k][c] !== finderA[k]) matchA = false
        if (matrix[r + k][c] !== finderB[k]) matchB = false
        if (!matchA && !matchB) break
      }
      if (matchA) score += 40
      if (matchB) score += 40
    }
  }

  // Rule 4: dark module proportion penalty → +10 per 5% deviation from 50%
  let darkCount = 0
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (matrix[r][c] === 1) darkCount++
    }
  }
  const percent = (darkCount * 100) / (size * size)
  const prevFive = Math.floor(percent / 5) * 5
  const nextFive = prevFive + 5
  score += Math.min(Math.abs(prevFive - 50) / 5, Math.abs(nextFive - 50) / 5) * 10

  return score
}

// ---------- Main QR generation ----------
function generateQR(text) {
  const bytes = encodeData(text)
  const version = selectVersion(bytes.length)
  const dataCW = buildDataCodewords(bytes, version)
  const finalCW = interleave(dataCW, version)

  // Convert to bits
  const bits = []
  for (const cw of finalCW) {
    for (let i = 7; i >= 0; i--) bits.push((cw >> i) & 1)
  }

  const { matrix, reserved, size } = createMatrix(version)

  // Place patterns
  placeFinder(matrix, reserved, 0, 0)
  placeFinder(matrix, reserved, 0, size - 7)
  placeFinder(matrix, reserved, size - 7, 0)
  placeAlignment(matrix, reserved, version)
  placeTiming(matrix, reserved, size)
  reserveFormatAndVersion(matrix, reserved, size, version)
  placeData(matrix, reserved, size, bits)

  // Find best mask
  let bestMask = 0, bestScore = Infinity
  for (let m = 0; m < 8; m++) {
    const masked = applyMask(matrix, reserved, size, m)
    placeFormatInfo(masked, size, m)
    placeVersionInfo(masked, size, version)
    const score = penaltyScore(masked, size)
    if (score < bestScore) { bestScore = score; bestMask = m }
  }

  const result = applyMask(matrix, reserved, size, bestMask)
  placeFormatInfo(result, size, bestMask)
  placeVersionInfo(result, size, version)

  return { modules: result, size }
}

/**
 * Draw QR code on a WeChat mini program canvas (2D API).
 * @param {Object} canvas - Canvas instance from wx.createSelectorQuery
 * @param {string} text - Content to encode
 * @param {number} canvasSize - Canvas width/height in px
 * @param {Object} options - { foreground, background, margin }
 */
function drawQRCode(canvas, text, canvasSize, options = {}) {
  const { foreground = '#000000', background = '#FFFFFF', margin = 2 } = options
  const ctx = canvas.getContext('2d')
  const dpr = wx.getWindowInfo().pixelRatio || 2

  canvas.width = canvasSize * dpr
  canvas.height = canvasSize * dpr
  ctx.scale(dpr, dpr)

  const { modules, size } = generateQR(text)
  const cellSize = (canvasSize - margin * 2) / size

  // Background
  ctx.fillStyle = background
  ctx.fillRect(0, 0, canvasSize, canvasSize)

  // Draw modules
  ctx.fillStyle = foreground
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (modules[r][c] === 1) {
        ctx.fillRect(
          margin + c * cellSize,
          margin + r * cellSize,
          Math.ceil(cellSize),
          Math.ceil(cellSize)
        )
      }
    }
  }
}

module.exports = { generateQR, drawQRCode }
