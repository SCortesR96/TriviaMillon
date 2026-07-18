function playerSession(prefilledCode) {
  return {
    screen: 'join', // join | waiting | question | reveal | ended | kicked
    code: prefilledCode || '',
    nickname: '',
    errorMessage: '',
    paused: false,
    ws: null,
    playerId: null,
    playersCount: 0,
    question: null,
    hasAnswered: false,
    selectedOptionId: null,
    revealData: null,
    leaderboard: [],

    join() {
      if (!this.code.trim() || !this.nickname.trim()) return;
      this.errorMessage = '';
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
      this.ws = new WebSocket(`${protocol}://${location.host}/ws/game/`);
      this.ws.addEventListener('open', () => {
        this.ws.send(JSON.stringify({
          type: 'join', role: 'player', code: this.code.trim().toUpperCase(), nickname: this.nickname.trim(),
        }));
      });
      this.ws.addEventListener('message', (event) => this._handleMessage(JSON.parse(event.data)));
      this.ws.addEventListener('close', () => {
        if (this.screen !== 'ended' && this.screen !== 'kicked') {
          this.errorMessage = 'Se perdio la conexion con el servidor.';
        }
      });
    },

    answer(optionId) {
      if (this.hasAnswered || this.paused) return;
      this.selectedOptionId = optionId;
      this.hasAnswered = true;
      this.ws.send(JSON.stringify({ type: 'answer', option_id: optionId }));
    },

    myResult() {
      if (!this.revealData) return null;
      return this.revealData.answers.find((a) => a.player_id === this.playerId) || null;
    },

    myRank() {
      const index = this.leaderboard.findIndex((p) => p.id === this.playerId);
      return index === -1 ? null : index + 1;
    },

    myScore() {
      const mine = this.leaderboard.find((p) => p.id === this.playerId);
      return mine ? mine.score : 0;
    },

    optionColor(index) {
      return ['bg-red-600', 'bg-blue-600', 'bg-yellow-500', 'bg-emerald-600'][index % 4];
    },

    _handleMessage(message) {
      switch (message.event) {
        case 'joined':
          this.playerId = message.player_id;
          // Si la partida ya esta en curso (reconexion), el servidor manda enseguida
          // un 'question_started' aparte con la pregunta activa (ver mas abajo).
          this.screen = 'waiting';
          break;
        case 'error':
          this.errorMessage = message.detail;
          break;
        case 'player_joined':
          this.playersCount = message.players.length;
          break;
        case 'question_started':
          this.screen = 'question';
          this.question = message;
          this.hasAnswered = !!message.already_answered;
          this.selectedOptionId = null;
          this.paused = false;
          window.TriviaSounds.playQuestionStart();
          break;
        case 'answer_revealed':
          this.screen = 'reveal';
          this.revealData = message;
          {
            const mine = this.myResult();
            const isCorrect = mine && mine.selected_option_id === message.correct_option_id;
            if (isCorrect) {
              window.TriviaSounds.playCorrect();
            } else {
              window.TriviaSounds.playIncorrect();
            }
          }
          break;
        case 'paused':
          this.paused = true;
          break;
        case 'resumed':
          this.paused = false;
          break;
        case 'game_ended':
          this.screen = 'ended';
          this.leaderboard = message.leaderboard;
          window.TriviaSounds.playGameEnd();
          break;
        case 'kicked':
          this.screen = 'kicked';
          break;
      }
    },
  };
}
