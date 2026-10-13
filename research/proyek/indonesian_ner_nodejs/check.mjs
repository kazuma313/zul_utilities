// Checks that the model in Node.js answers like the original PyTorch model.
//
//   node check.mjs
//
// reference.json (written by export_onnx.py) holds, for every line of samples.txt, PyTorch's token ids, logits,
// labels, and the entities of Python's pipeline with aggregation_strategy="first". This file compares all four.

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadNer } from './ner.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const LOGIT_TOLERANCE = 1e-3;
const SCORE_TOLERANCE = 1e-3;

const reference = JSON.parse(readFileSync(join(HERE, 'reference.json'), 'utf8'));
const ner = await loadNer();
const { tokenizer, model } = ner;

let failures = 0;
let largest = 0;
const fail = (text, what) => {
    failures += 1;
    console.log(`  FAIL ${what}\n       in: ${text}`);
};

for (const row of reference) {
    const inputs = tokenizer(row.text);
    const ids = Array.from(inputs.input_ids.data, Number);
    if (JSON.stringify(ids) !== JSON.stringify(row.input_ids)) fail(row.text, 'token ids differ from Python');

    const { logits } = await model(inputs);
    const labels = logits.dims[2];
    for (let t = 0; t < row.logits.length; ++t) {
        for (let k = 0; k < labels; ++k) {
            largest = Math.max(largest, Math.abs(logits.data[t * labels + k] - row.logits[t][k]));
        }
    }

    const { entities } = await ner(row.text);
    const ours = entities.map((e) => `${e.type}|${e.text}|${e.start}|${e.end}`);
    const theirs = row.entities.map((e) => `${e.type}|${e.text}|${e.start}|${e.end}`);
    if (JSON.stringify(ours) !== JSON.stringify(theirs)) {
        fail(row.text, `entities differ\n       node:   ${ours.join('; ')}\n       python: ${theirs.join('; ')}`);
    }
    entities.forEach((e, i) => {
        if (row.entities[i] && Math.abs(e.score - row.entities[i].score) > SCORE_TOLERANCE) {
            fail(row.text, `score of "${e.text}": node ${e.score.toFixed(4)}, python ${row.entities[i].score}`);
        }
    });
}

if (largest > LOGIT_TOLERANCE) fail('(all sentences)', `largest logit difference ${largest.toExponential(2)} > ${LOGIT_TOLERANCE}`);
const entityCount = reference.reduce((n, r) => n + r.entities.length, 0);
console.log(`${reference.length} sentences, ${entityCount} entities; largest logit difference ${largest.toExponential(2)}`);
console.log(failures ? `${failures} differences` : 'OK: token ids, logits and entities match the PyTorch model');
process.exitCode = failures ? 1 : 0;
