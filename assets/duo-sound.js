/* Duo sound engine
   The canonical feedback sounds for every lesson in a teach-duo workspace.

   Sounds are synthesised with the Web Audio API rather than shipped as audio
   files. That keeps a lesson a single self-contained HTML file with no binary
   assets, no CDN, and nothing to load over the network.

   Browsers refuse to start audio before a user gesture, so the context is
   created on the first call and resumed if it starts suspended. Every method
   is safe to call before that first gesture, and safe to call in an
   environment with no audio support at all.
*/
(function (global) {
  "use strict";

  var STORAGE_KEY = "teach-duo:muted";

  function supported() {
    return typeof global.AudioContext === "function" ||
           typeof global.webkitAudioContext === "function";
  }

  function readMuted() {
    try {
      return global.localStorage.getItem(STORAGE_KEY) === "1";
    } catch (error) {
      return false;
    }
  }

  function writeMuted(value) {
    try {
      global.localStorage.setItem(STORAGE_KEY, value ? "1" : "0");
    } catch (error) {
      /* storage unavailable, stay muted for this page only */
    }
  }

  var context = null;
  var master = null;

  function ensureContext() {
    if (!supported()) return null;
    if (!context) {
      var Ctor = global.AudioContext || global.webkitAudioContext;
      try {
        context = new Ctor();
      } catch (error) {
        return null;
      }
      master = context.createGain();
      master.gain.value = 0.9;
      master.connect(context.destination);
    }
    if (context.state === "suspended" && context.resume) {
      context.resume();
    }
    return context;
  }

  /* One shaped tone. `when` is seconds from now, `dur` is seconds. */
  function tone(when, freq, dur, type, peak) {
    var ctx = context;
    var start = ctx.currentTime + when;
    var stop = start + dur;

    var osc = ctx.createOscillator();
    osc.type = type || "sine";
    osc.frequency.setValueAtTime(freq, start);

    var gain = ctx.createGain();
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(peak, start + dur * 0.18);
    gain.gain.exponentialRampToValueAtTime(0.0001, stop);

    osc.connect(gain);
    gain.connect(master);
    osc.start(start);
    osc.stop(stop + 0.02);
  }

  /* A short pitch slide, used for the falling "wrong" tone. */
  function slide(when, from, to, dur, type, peak) {
    var ctx = context;
    var start = ctx.currentTime + when;
    var stop = start + dur;

    var osc = ctx.createOscillator();
    osc.type = type || "triangle";
    osc.frequency.setValueAtTime(from, start);
    osc.frequency.exponentialRampToValueAtTime(to, stop);

    var gain = ctx.createGain();
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(peak, start + dur * 0.12);
    gain.gain.exponentialRampToValueAtTime(0.0001, stop);

    osc.connect(gain);
    gain.connect(master);
    osc.start(start);
    osc.stop(stop + 0.02);
  }

  var muted = readMuted();

  var sounds = {
    /* A soft tick when an answer is selected. */
    select: function () {
      tone(0, 880, 0.045, "sine", 0.05);
    },

    /* Bright and rising: the answer was right. */
    correct: function () {
      tone(0, 659.25, 0.12, "sine", 0.16);   // E5
      tone(0.09, 987.77, 0.20, "sine", 0.16); // B5
    },

    /* Low and falling: the answer was wrong. */
    wrong: function () {
      slide(0, 320, 180, 0.22, "square", 0.09);
      tone(0.16, 165, 0.24, "triangle", 0.10);
    },

    /* One heart gone. */
    heartLost: function () {
      slide(0, 440, 220, 0.28, "triangle", 0.10);
    },

    /* XP counter moving. */
    xp: function () {
      tone(0, 1046.5, 0.07, "sine", 0.09);   // C6
      tone(0.06, 1396.9, 0.11, "sine", 0.07); // F6
    },

    /* Lesson finished. */
    complete: function () {
      tone(0.00, 523.25, 0.14, "triangle", 0.14); // C5
      tone(0.11, 659.25, 0.14, "triangle", 0.14); // E5
      tone(0.22, 783.99, 0.14, "triangle", 0.14); // G5
      tone(0.33, 1046.5, 0.34, "triangle", 0.16); // C6, held
    },

    /* Out of hearts. */
    fail: function () {
      slide(0, 392, 147, 0.42, "sawtooth", 0.10);
      tone(0.34, 110, 0.30, "sawtooth", 0.09);
    }
  };

  global.DuoSound = {
    /* Play a named sound. Unknown names and muted state are no-ops. */
    play: function (name) {
      if (muted) return false;
      var sound = sounds[name];
      if (!sound) return false;
      if (!ensureContext()) return false;
      try {
        sound();
      } catch (error) {
        return false;
      }
      return true;
    },

    isMuted: function () {
      return muted;
    },

    setMuted: function (value) {
      muted = !!value;
      writeMuted(muted);
      return muted;
    },

    toggle: function () {
      return global.DuoSound.setMuted(!muted);
    },

    /* Sound effects for a learner with reduced-motion or audio sensitivity. */
    isSupported: supported,

    available: Object.keys(sounds)
  };
})(typeof window !== "undefined" ? window : globalThis);