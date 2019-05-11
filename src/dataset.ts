import * as assert from 'assert';

import { shuffle } from './utils';

export const MAX_CHAR = 28;

const MIN_SEQUENCE = 8;

// Moving average window
const WINDOW = 7;

export type InputEntry = {
  readonly e: 'u' | 'd';
  readonly k: string;
  readonly ts: number;
} | 'r';

export interface ISequenceElem {
  readonly code: number;
  readonly hold: number;
  readonly duration: number;
}

export type Sequence = ReadonlyArray<ISequenceElem>;

export type Input = ReadonlyArray<InputEntry>;
export type Output = ReadonlyArray<Sequence>;

type IntermediateEntry = 'reset' | 'invalid' | ISequenceElem;

function normalize(sequence: Sequence): ISequenceElem[] {
  let mean = 0;
  for (const elem of sequence) {
    mean += elem.duration;
  }
  mean /= sequence.length;
  return sequence.map((elem) => {
    return {
      code: elem.code,
      hold: elem.hold / mean,
      duration: elem.duration / mean,
    };
  });
}

export class Dataset {
  constructor(private readonly sentences: string[]) {
  }

  public generate(events: Input): Output {
    const filtered: InputEntry[] = [];

    // Filter events
    const index = { sentence: 0, letter: 0 };
    const pressed = new Set();
    for (const event of events) {
      // TODO(indutny): do we care?
      if (event === 'r') {
        index.letter = 0;
        index.sentence++;
        pressed.clear();
        filtered.push('r');
        continue;
      }

      const key = event.k;
      const kind = event.e;

      const sentence = this.sentences[index.sentence] || '';
      const letter = sentence[index.letter] || null;

      if (kind === 'd' && key === letter) {
        if (/^[a-zA-Z ,\.]$/.test(key)) {
          pressed.add(key);
          filtered.push(event);
        }

        index.letter++;
      } else if (kind === 'u' && pressed.has(key)) {
        pressed.delete(key);
        filtered.push(event);
      }
    }

    // Just a safe-guard
    if (filtered[filtered.length - 1] !== 'r') {
      filtered.push('r');
    }

    const info: Map<string, { duration: number, start: number }> = new Map();

    const out: ISequenceElem[][] = [];
    let sequence: ISequenceElem[] = [];
    for (const [ i, event ] of filtered.entries()) {
      if (event === 'r') {
        info.clear();
        if (sequence.length !== 0) {
          out.push(normalize(sequence));
        }
        sequence = [];
        continue;
      }

      if (event.e === 'd') {
        let j = i + 1;
        let next = event;
        for (let j = i + 1; j < filtered.length; j++) {
          const entry = filtered[j];
          if (entry !== 'r' && entry.e === 'd') {
            next = entry;
            break;
          }
        }

        // Time delta between two presses
        assert.strictEqual(next.e, 'd');
        const duration = next.ts - event.ts;

        info.set(event.k, { duration, start: event.ts });
        continue;
      }

      const prev = info.get(event.k)!;
      const hold = event.ts - prev.start;
      info.delete(event.k);

      sequence.push({
        code: this.compress(event.k.charCodeAt(0)),
        hold,
        duration: prev.duration,
      });
    }
    if (sequence.length !== 0) {
      out.push(normalize(sequence));
      sequence = [];
    }

    return out;
  }

  private compress(code: number): number {
    // 'abcdefghijklmnopqrstuvwxyz ,.'
    // a - z
    if (0x61 <= code && code <= 0x7a) {
      return code - 0x61;

    // A - Z
    } else if (0x41 <= code && code <= 0x5a) {
      return code - 0x41;

    // ' '
    } else if (code === 0x20) {
      return 26;

    // ','
    } else if (code === 0x2c) {
      return 27;

    // '.'
    } else if (code === 0x2e) {
      return 28;
    } else {
      throw new Error('Unexpected code: ' + code.toString(16));
    }
  }
}
