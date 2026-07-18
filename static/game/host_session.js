function hostSession(code, hostToken) {
  return {
    screen: 'connecting', // connecting | lobby | question | reveal | ended | fatal_error
    statusMessage: '',
    errorMessage: '',
    players: [],
    question: null,
    answeredPlayerIds: new Set(),
    revealData: null,
    leaderboard: [],
    timerSeconds: 0,
    _timerId: null,
    ws: null,

    init() {
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
      this.ws = new WebSocket(`${protocol}://${location.host}/ws/game/`);
      this.ws.addEventListener('open', () => {
        this.ws.send(JSON.stringify({ type: 'join', role: 'host', code, host_token: hostToken }));
      });
      this.ws.addEventListener('message', (event) => this._handleMessage(JSON.parse(event.data)));
      this.ws.addEventListener('close', () => {
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
          this._startTimer();
          break;
        case 'player_answered':
          this.answeredPlayerIds.add(message.player_id);
          break;
        case 'answer_revealed':
          this._stopTimer();
          this.screen = 'reveal';
          this.revealData = message;
          break;
        case 'game_ended':
          this._stopTimer();
          this.screen = 'ended';
          this.leaderboard = message.leaderboard;
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
        if (this.timerSeconds > 0) this.timerSeconds -= 1;
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
