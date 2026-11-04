const greek: Record<string, string> = {
  alpha: 'α', beta: 'β', gamma: 'γ', theta: 'θ', sigma: 'σ', mu: 'μ',
  nabla: '∇', pi: 'π',
}

const subscript: Record<string, string> = {
  '0': '₀', '1': '₁', '2': '₂', '3': '₃', '+': '₊', '-': '₋',
  a: 'ₐ', e: 'ₑ', h: 'ₕ', i: 'ᵢ', j: 'ⱼ', k: 'ₖ', l: 'ₗ', m: 'ₘ',
  n: 'ₙ', o: 'ₒ', p: 'ₚ', r: 'ᵣ', s: 'ₛ', t: 'ₜ', u: 'ᵤ', v: 'ᵥ',
  x: 'ₓ',
}

const superscript: Record<string, string> = { '2': '²', '3': '³', '*': '*' }
const operators: Record<string, string> = {
  max: 'max', min: 'min', ln: 'ln', sum: 'Σ', propto: '∝', in: '∈',
  cdot: '·', times: '×', neq: '≠', leq: '≤', geq: '≥', le: '≤', ge: '≥', approx: '≈',
  ominus: '⊖', oplus: '⊕', circ: '∘', bullet: '•',
}

function scriptText(value: string, alphabet: Record<string, string>, prefix: string) {
  if (![...value].every((char) => alphabet[char])) return `${prefix}(${value})`
  return [...value].map((char) => alphabet[char]).join('')
}

function readGroup(source: string, start: number): [string, number] | undefined {
  if (source[start] !== '{') return undefined
  let depth = 0
  for (let index = start; index < source.length; index += 1) {
    if (source[index] === '{') depth += 1
    if (source[index] === '}') depth -= 1
    if (depth === 0) return [source.slice(start + 1, index), index + 1]
  }
  return undefined
}

function replaceFractions(source: string) {
  let output = ''
  let cursor = 0
  while (cursor < source.length) {
    const start = source.indexOf('\\frac', cursor)
    if (start < 0) return output + source.slice(cursor)
    const numerator = readGroup(source, start + 5)
    const denominator = numerator && readGroup(source, numerator[1])
    if (!numerator || !denominator) {
      output += source.slice(cursor, start + 5)
      cursor = start + 5
      continue
    }
    output += `${source.slice(cursor, start)}(${numerator[0]}) / (${denominator[0]})`
    cursor = denominator[1]
  }
  return output
}

/** Convert the registry's small LaTeX subset into readable, safe text. */
export function formatFormula(source: string) {
  let formula = source
    .replace(/\\begin\{cases\}/g, '{ ')
    .replace(/\\end\{cases\}/g, ' }')
    .replace(/\\text\{([^{}]*)\}/g, '$1')
    .replace(/\\mathrm\{([^{}]*)\}/g, '$1')
    .replace(/\\operatorname\{([^{}]*)\}/g, '$1')

  let previous = ''
  while (previous !== formula) {
    previous = formula
    formula = replaceFractions(formula)
  }

  formula = formula
    .replace(/\\sqrt\{([^{}]*)\}/g, '√($1)')
    .replace(/\\sum_\{([^{}]*)\}/g, 'Σ ($1)')
    .replace(/\\arg\\max/g, 'arg max')
    .replace(/\\bar\s*f/g, 'f̄')
    .replace(/\\(alpha|beta|gamma|theta|sigma|mu|nabla|pi)(?=_|[^A-Za-z])/g, (_, name: string) => greek[name])
    .replace(/\\(max|min|ln|sum|propto|in|cdot|times|neq|leq|geq|le|ge|approx|ominus|oplus|circ|bullet)(?=_|[^A-Za-z])/g, (_, name: string) => operators[name])
    .replace(/\\#/g, '#')
    .replace(/\\\{/g, '{')
    .replace(/\\\}/g, '}')
    .replace(/\\left|\\right/g, '')
    .replace(/\\(quad|,|;|!|:)/g, ' ')
    .replace(/\\\s/g, ' ')
    .replace(/\\\\/g, '; ')
    .replace(/\^\{([^{}]+)\}/g, '^$1')
    .replace(/&/g, ' if ')
    .replace(/\^\{?([23])\}?/g, (_, value: string) => superscript[value])
    .replace(/_\{([^{}]+)\}/g, (_, value: string) => scriptText(value, subscript, '_'))
    .replace(/_([A-Za-z0-9])/g, (_, value: string) => scriptText(value, subscript, '_'))
    .replace(/\bif\s+otherwise\b/g, 'otherwise')
    .replace(/[{}]/g, (brace) => brace)
    .replace(/\s+/g, ' ')
    .replace(/\s+([,;)])/g, '$1')
    .replace(/([(])\s+/g, '$1')
    .trim()

  return formula
}
