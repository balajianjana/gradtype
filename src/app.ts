import * as wilde from '../data/wilde.txt';
import leven = require('leven');
import * as performance from './performance';

const API_ENDPOINT = 'https://gradtype-survey.darksi.de/';
const LS_KEY = 'gradtype-survey-v1';
const INITIAL_COUNTER = 90;
const TOLERANCE = 0.5;

const elems = {
  firefox: document.getElementById('firefox')!,
  collect: document.getElementById('collect')!,

  display: document.getElementById('display')!,
  input: document.getElementById('input')! as HTMLInputElement,
  download: document.getElementById('download')!,
  counter: document.getElementById('counter')!,
  wrap: document.getElementById('wrap')!,
};

if (performance.detect()) {
  elems.collect.style.display = 'inherit';
} else {
  elems.firefox.style.display = 'inherit';
}

interface ILogEvent {
  readonly ts: number;
  readonly k: string;
}

const text: string = wilde.toString().replace(/\s+/g, ' ');
const sentences = text.split(/\.+/g)
  .filter((line) => !/["?!]/.test(line))
  .map((line) => line.trim())
  .filter((line) => line.length > 15);

let index = 0xdeadbeef % sentences.length;

let counter = INITIAL_COUNTER;
elems.counter.textContent = counter.toString();

const log: ILogEvent[] = [];

function next() {
  const prior = (elems.display.textContent || '').trim();

  const entered = elems.input.value;
  if (prior !== '') {
    const distance = leven(entered, prior);

    // Remove last sentence
    if (entered.length < 5 || distance > TOLERANCE * prior.length) {
      let i: number = 0;
      for (i = log.length - 1; i >= 0; i--) {
        if (log[i].k === '.') {
          break;
        }
      }

      log.splice(i, log.length - i);
      elems.input.value = '';
      return;
    }
  }

  let sentence;
  do {
    sentence = sentences[index++];
    if (index === sentences.length) {
      index = 0;
    }
  } while (sentence.length > 60 || sentence.length < 30);

  elems.display.textContent = sentence + '.';

  elems.input.focus();
  elems.input.value = '';
  elems.counter.textContent = counter.toString();

  if (counter-- === 0) {
    save();
  }
}

const start = performance.now();
elems.input.onkeypress = (e: KeyboardEvent) => {
  log.push({ ts: performance.now(), k: e.key });

  if (e.key === '.') {
    next();
    e.preventDefault();
    return;
  }
};

function save() {
  const json = JSON.stringify(log.map((event) => {
    return { ts: (event.ts - start) / 1000, k: event.k };
  }));

  elems.wrap.innerHTML =
    '<h1>Uploading, please do not close this window...</h1>';

  const xhr = new XMLHttpRequest();

  xhr.onload = () => {
    let response: any;
    try {
      response = JSON.parse(xhr.responseText);
    } catch (e) {
      error();
      return;
    }

    if (!response.code) {
      error();
      return;
    }

    complete(response.code);
  };

  xhr.onerror = () => {
    error();
  };

  xhr.open('PUT', API_ENDPOINT, true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.send(json);
};

function complete(code?: string) {
  if (window.localStorage) {
    window.localStorage.setItem(LS_KEY, 'submitted');
  }
  if (code === undefined) {
    elems.wrap.innerHTML = '<h1>Thank you for submitting survey!</h1>';
  } else {
    elems.wrap.innerHTML = '<h1>Thank you for submitting survey!</h1>' +
      `<h1 style="color:red">Your code is ${code}</h1>`;
  }
}

function error() {
  elems.wrap.innerHTML = '<h1>Server error, please retry later!</h1>';
}

if (window.localStorage && window.localStorage.getItem(LS_KEY)) {
  complete();
} else {
  next();
}