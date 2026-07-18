window.TriviaSounds = (function () {
  let ctx = null;

  function getContext() {
    if (!ctx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      ctx = new AudioContextClass();
    }
    return ctx;
  }

  function tone(frequency, durationMs, type, startDelayMs) {
    try {
      const audioCtx = getContext();
      const oscillator = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      oscillator.type = type || 'sine';
      oscillator.frequency.value = frequency;
      const startAt = audioCtx.currentTime + (startDelayMs || 0) / 1000;
      gain.gain.setValueAtTime(0.15, startAt);
      gain.gain.exponentialRampToValueAtTime(0.001, startAt + durationMs / 1000);
      oscillator.connect(gain);
      gain.connect(audioCtx.destination);
      oscillator.start(startAt);
      oscillator.stop(startAt + durationMs / 1000);
    } catch (e) {
      // Web Audio no disponible/bloqueado por el navegador: el juego sigue funcionando sin sonido.
    }
  }

  return {
    playQuestionStart() {
      tone(440, 120);
    },
    playCorrect() {
      tone(523.25, 150); // C5
      tone(783.99, 220, 'sine', 140); // G5
    },
    playIncorrect() {
      tone(196.0, 350, 'sawtooth');
    },
    playGameEnd() {
      tone(523.25, 150);
      tone(659.25, 150, 'sine', 150);
      tone(783.99, 300, 'sine', 300);
    },
  };
})();
