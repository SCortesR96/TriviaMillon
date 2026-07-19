function hostSession(code, hostToken) {
  return {
    screen: 'connecting', // connecting | lobby | question | reveal | ended | fatal_error
    statusMessage: '',
    errorMessage: '',
    paused: false,
    players: [],
    question: null,
    answeredPlayerIds: new Set(),
    revealData: null,
    leaderboard: [],
    timerSeconds: 0,
    _timerId: null,
    _heartbeatId: null,
    ws: null,

    init() {
      if (this.ws) return; // evita abrir una segunda conexion si init() llega a correr mas de una vez
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
      const socket = new WebSocket(`${protocol}://${location.host}/ws/game/`);
      this.ws = socket;
      socket.addEventListener('open', () => {
        socket.send(JSON.stringify({ type: 'join', role: 'host', code, host_token: hostToken }));
        // Mantiene viva la conexion durante pausas largas (ej. leyendo la pregunta en voz
        // alta) para que un proxy de por medio no la cierre por inactividad.
        this._heartbeatId = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' }));
        }, 25000);
      });
      socket.addEventListener('message', (event) => this._handleMessage(JSON.parse(event.data)));
      socket.addEventListener('close', () => {
        if (this.ws !== socket) return; // una conexion vieja se cerro, ya no es la activa
        clearInterval(this._heartbeatId);
        if (this.screen !== 'ended') {
          this.errorMessage = 'Se perdio la conexion con el servidor.';
        }
      });
    },

    _handleMessage(message) {
      switch (message.event) {
        case 'joined':
          this.screen = 'lobby';
          this.players = message.players;
          break;
        case 'error':
          this.errorMessage = message.detail;
          if (this.screen === 'connecting') this.screen = 'fatal_error';
          break;
        case 'player_joined':
          this.players = message.players;
          break;
        case 'question_started':
          this.screen = 'question';
          this.question = message;
          this.answeredPlayerIds = new Set();
          this.paused = false;
          this._startTimer();
          window.TriviaSounds.playQuestionStart();
          break;
        case 'player_answered':
          this.answeredPlayerIds.add(message.player_id);
          break;
        case 'answer_revealed':
          this._stopTimer();
          this.screen = 'reveal';
          this.revealData = message;
          break;
        case 'paused':
          this.paused = true;
          break;
        case 'resumed':
          this.paused = false;
          break;
        case 'game_ended':
          this._stopTimer();
          this.screen = 'ended';
          this.leaderboard = message.leaderboard;
          window.TriviaSounds.playGameEnd();
          break;
      }
    },

    start() {
      this.ws.send(JSON.stringify({ type: 'start' }));
    },

    reveal() {
      this.ws.send(JSON.stringify({ type: 'reveal' }));
    },

    next() {
      this.ws.send(JSON.stringify({ type: 'next' }));
    },

    skip() {
      if (confirm('¿Saltar esta pregunta sin revelar la respuesta?')) {
        this.ws.send(JSON.stringify({ type: 'next' }));
      }
    },

    togglePause() {
      this.ws.send(JSON.stringify({ type: this.paused ? 'resume' : 'pause' }));
    },

    kick(playerId) {
      if (confirm('¿Expulsar a este jugador de la sala?')) {
        this.ws.send(JSON.stringify({ type: 'kick', player_id: playerId }));
      }
    },

    end() {
      if (confirm('¿Terminar la partida ahora?')) {
        this.ws.send(JSON.stringify({ type: 'end' }));
      }
    },

    answeredCount() {
      return this.answeredPlayerIds.size;
    },

    _startTimer() {
      this._stopTimer();
      this.timerSeconds = 20;
      this._timerId = setInterval(() => {
        if (!this.paused && this.timerSeconds > 0) this.timerSeconds -= 1;
      }, 1000);
    },

    _stopTimer() {
      if (this._timerId) {
        clearInterval(this._timerId);
        this._timerId = null;
      }
    },
  };
}
