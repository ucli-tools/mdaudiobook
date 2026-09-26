// sre_batch.js: speak a batch of MathML expressions with the Speech Rule Engine.
// stdin: JSON {"style": "clearspeak", "items": ["<math>...</math>" | null, ...]}
// stdout: JSON list of spoken strings (null where the input was null).
const sre = require('speech-rule-engine');

let input = '';
process.stdin.on('data', d => (input += d));
process.stdin.on('end', async () => {
  const job = JSON.parse(input);
  await sre.setupEngine({ domain: job.style || 'clearspeak', modality: 'speech', locale: 'en' });
  await sre.engineReady();
  const out = job.items.map(m => {
    if (!m) return null;
    try {
      return sre.toSpeech(m);
    } catch (e) {
      return null;
    }
  });
  process.stdout.write(JSON.stringify(out));
});
