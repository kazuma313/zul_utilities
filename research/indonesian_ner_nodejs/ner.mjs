// Named entity recognition for Indonesian text in Node.js, with cahya/bert-base-indonesian-NER converted to ONNX.
//
//   node ner.mjs "Presiden Joko Widodo meresmikan Bendungan Jatigede di Sumedang."
//   node ner.mjs --file samples.txt
//   node ner.mjs --json "teks"        (the entities as JSON)
//
// The model must first be converted with export_onnx.py; it is read from models/, never downloaded here.
//
// transformers.js has a token-classification pipeline, but its "simple" grouping works on word pieces, gives no
// character offsets and returns lower case text ("joko widodo"). This file does what Python's
// aggregation_strategy="first" does instead: a word takes the label of its first piece, words are joined into
// entities by their B-/I- tags, and every entity is cut from the original text with its start and end.

import { AutoModelForTokenClassification, AutoTokenizer, env, softmax } from '@huggingface/transformers';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const MODEL_ID = 'cahya/bert-base-indonesian-NER';
const HERE = dirname(fileURLToPath(import.meta.url));

// The 19 entity types. The model card does not name its training data, but its 39 labels are those of the NERGrit
// corpus, in the same order (huggingface.co/datasets/grit-id/id_nergrit_corpus), so these are NERGrit's meanings.
export const ENTITY_TYPES = {
    CRD: 'bilangan', DAT: 'tanggal', EVT: 'peristiwa', FAC: 'fasilitas', GPE: 'entitas geopolitik (negara, provinsi, kota)',
    LAN: 'bahasa', LAW: 'hukum, seperti undang-undang', LOC: 'lokasi', MON: 'uang', NOR: 'organisasi politik',
    ORD: 'urutan', ORG: 'organisasi', PER: 'orang', PRC: 'persentase', PRD: 'produk', QTY: 'kuantitas',
    REG: 'agama', TIM: 'waktu', WOA: 'karya seni',
};

// BERT reads at most 512 pieces, two of them [CLS] and [SEP]. A longer text is cut into parts, at a sentence end
// when there is one in the second half of the part, else between two words.
export const MAX_PIECES = 510;

/**
 * Loads the tokenizer and the ONNX model from models/ and returns ner(text), any length.
 * ner.tokenizer and ner.model are the loaded objects, for code that needs them directly.
 *
 * @param {{ modelDir?: string }} [options] the folder that holds models/<MODEL_ID>
 * @returns {Promise<((text: string) => Promise<{ entities: Entity[], words: Word[] }>) & { tokenizer: any, model: any }>}
 */
export async function loadNer({ modelDir = join(HERE, 'models') } = {}) {
    env.localModelPath = modelDir;
    env.allowRemoteModels = false;
    const tokenizer = await AutoTokenizer.from_pretrained(MODEL_ID);
    const model = await AutoModelForTokenClassification.from_pretrained(MODEL_ID, { dtype: 'fp32' });
    const id2label = model.config.id2label;

    async function nerPart(text) {
        const pieces = tokenizer.tokenize(text);                 // without [CLS] and [SEP]
        const { logits } = await model(tokenizer(text, { truncation: true }));
        const [, length, labels] = logits.dims;
        const spans = alignPieces(text, pieces);

        // One row per word piece: skip [CLS] (row 0) and stop before [SEP].
        const scored = [];
        for (let i = 0; i < Math.min(pieces.length, length - 2); ++i) {
            const probabilities = softmax(Array.from(logits.data.subarray((i + 1) * labels, (i + 2) * labels)));
            let best = 0;
            for (let k = 1; k < labels; ++k) if (probabilities[k] > probabilities[best]) best = k;
            scored.push({ piece: pieces[i], label: id2label[best], score: probabilities[best], ...spans[i] });
        }
        const words = wordsOf(scored, text);
        return { entities: entitiesOf(words, text), words };
    }

    async function ner(text) {
        const pieces = tokenizer.tokenize(text);
        if (pieces.length <= MAX_PIECES) return nerPart(text);
        const spans = alignPieces(text, pieces);
        const entities = [];
        const words = [];
        for (let from = 0; from < pieces.length;) {
            const to = cutAt(pieces, from);
            const offset = spans[from].start;
            const part = await nerPart(text.slice(offset, spans[to - 1].end));
            const shift = (x) => ({ ...x, start: x.start + offset, end: x.end + offset });
            entities.push(...part.entities.map(shift));
            words.push(...part.words.map(shift));
            from = to;
        }
        return { entities, words };
    }

    return Object.assign(ner, { tokenizer, model });
}

/** The end (exclusive) of the part that starts at piece `from`. */
function cutAt(pieces, from) {
    const limit = from + MAX_PIECES;
    if (limit >= pieces.length) return pieces.length;
    for (let i = limit; i > from + MAX_PIECES / 2; --i) {
        if (/^[.!?]$/.test(pieces[i - 1]) && !pieces[i].startsWith('##')) return i;
    }
    let cut = limit;
    while (cut > from + 1 && pieces[cut].startsWith('##')) --cut;
    return cut;
}

/**
 * @typedef {{ text: string, label: string, score: number, start: number, end: number }} Word
 * @typedef {{ type: string, text: string, start: number, end: number, score: number }} Entity
 */

// ---------------------------------------------------------------------------
// Pieces -> words -> entities
// ---------------------------------------------------------------------------

/**
 * Finds every word piece in the original text. The tokenizer lowercases and drops accents, so the search runs on a
 * normalised copy that remembers, for each of its characters, where it came from.
 */
export function alignPieces(text, pieces) {
    let normal = '';
    const origin = [];
    for (let i = 0; i < text.length; ++i) {
        const folded = text[i].normalize('NFD').replace(/\p{Mn}/gu, '').toLowerCase();
        for (const ch of folded) {
            normal += ch;
            origin.push(i);
        }
    }
    let cursor = 0;
    return pieces.map((piece, i) => {
        const bare = piece.startsWith('##') ? piece.slice(2) : piece;
        while (cursor < normal.length && /\s/.test(normal[cursor])) ++cursor;
        let at = bare === '[UNK]' ? -1 : normal.indexOf(bare, cursor);
        if (at === -1) {
            // [UNK] or a piece we cannot find: it covers the text up to the next piece we can find.
            const next = pieces[i + 1]?.replace(/^##/, '');
            const stop = next ? normal.indexOf(next, cursor + 1) : -1;
            const end = stop === -1 ? Math.min(normal.length, cursor + 1) : stop;
            const span = { start: origin[cursor] ?? text.length, end: (origin[end - 1] ?? text.length - 1) + 1 };
            cursor = end;
            return span;
        }
        cursor = at + bare.length;
        return { start: origin[at], end: origin[cursor - 1] + 1 };
    });
}

/** A word starts at a piece without "##" and takes the label and score of that first piece. */
export function wordsOf(scored, text) {
    const words = [];
    for (const p of scored) {
        if (p.piece.startsWith('##') && words.length) {
            words[words.length - 1].end = p.end;
        } else {
            words.push({ label: p.label, score: p.score, start: p.start, end: p.end });
        }
    }
    return words.map((w) => ({ text: text.slice(w.start, w.end), ...w }));
}

/** Joins words into entities: same type and not a new B- continues; "O" words end an entity and are dropped. */
export function entitiesOf(words, text) {
    const groups = [];
    for (const w of words) {
        const [bi, type] = w.label.startsWith('B-') || w.label.startsWith('I-') ? [w.label[0], w.label.slice(2)] : ['I', w.label];
        const last = groups[groups.length - 1];
        if (last && last.type === type && bi !== 'B') {
            last.words.push(w);
        } else {
            groups.push({ type, words: [w] });
        }
    }
    return groups
        .filter((g) => g.type !== 'O')
        .map(({ type, words: ws }) => {
            const start = ws[0].start;
            const end = ws[ws.length - 1].end;
            const score = ws.reduce((sum, w) => sum + w.score, 0) / ws.length;
            return { type, text: text.slice(start, end), start, end, score };
        });
}

// ---------------------------------------------------------------------------
// Command line
// ---------------------------------------------------------------------------

async function main(argv) {
    const json = argv.includes('--json');
    const args = argv.filter((a) => a !== '--json');
    const fileAt = args.indexOf('--file');
    const texts = fileAt >= 0
        ? readFileSync(args[fileAt + 1], 'utf8').split(/\r?\n/).filter((line) => line.trim())
        : [args.join(' ')].filter((t) => t.trim());
    if (!texts.length) {
        console.error('Usage: node ner.mjs "teks" | node ner.mjs --file FILE [--json]');
        return 2;
    }

    const loading = performance.now();
    const ner = await loadNer();
    const loaded = performance.now() - loading;
    const results = [];
    let seconds = 0;
    for (const text of texts) {
        const started = performance.now();
        const { entities } = await ner(text);
        seconds += (performance.now() - started) / 1000;
        results.push({ text, entities });
    }

    if (json) {
        console.log(JSON.stringify(results, null, 1));
        return 0;
    }
    for (const { text, entities } of results) {
        console.log(`- ${text}`);
        for (const e of entities) console.log(`    ${e.type.padEnd(4)} ${e.text}  (${e.score.toFixed(4)}, ${ENTITY_TYPES[e.type] ?? ''})`);
    }
    console.log(`model loaded in ${(loaded / 1000).toFixed(1)} s; ${texts.length} texts in ${seconds.toFixed(2)} s`);
    return 0;
}

// Run as a command only when this file is the one Node started (not when imported, or from `node -e`).
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    process.exitCode = await main(process.argv.slice(2));
}
