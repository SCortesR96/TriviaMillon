from django.db import models

from apps.questions.models import AnswerOption, Question, QuestionSet


class LadderTemplate(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PrizeLevel(models.Model):
    ladder_template = models.ForeignKey(LadderTemplate, on_delete=models.CASCADE, related_name='levels')
    index = models.PositiveIntegerField()
    points = models.PositiveIntegerField()
    is_checkpoint = models.BooleanField(default=False)

    class Meta:
        ordering = ['ladder_template', 'index']
        constraints = [
            models.UniqueConstraint(fields=['ladder_template', 'index'], name='unique_level_index_per_ladder'),
        ]

    def __str__(self):
        return f'{self.ladder_template.name} - nivel {self.index} ({self.points} pts)'


class GameSession(models.Model):
    class Status(models.TextChoices):
        LOBBY = 'lobby', 'Lobby'
        IN_PROGRESS = 'in_progress', 'En curso'
        FINISHED = 'finished', 'Terminada'

    code = models.CharField(max_length=8, unique=True)
    host_token = models.CharField(max_length=64)
    question_set = models.ForeignKey(QuestionSet, on_delete=models.PROTECT, related_name='sessions')
    ladder_template = models.ForeignKey(LadderTemplate, on_delete=models.PROTECT, related_name='sessions')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LOBBY)
    current_level_index = models.PositiveIntegerField(default=0)
    is_paused = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Sala {self.code} ({self.status})'


class Player(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    nickname = models.CharField(max_length=50)
    client_token = models.CharField(max_length=64, blank=True)
    channel_name = models.CharField(max_length=100, blank=True)  # canal WS actual, para poder expulsarlo
    score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', 'joined_at']
        constraints = [
            models.UniqueConstraint(fields=['session', 'nickname'], name='unique_nickname_per_session'),
        ]

    def __str__(self):
        return f'{self.nickname} @ {self.session.code}'


class PlayerAnswer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name='+')
    selected_option = models.ForeignKey(AnswerOption, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    points_awarded = models.IntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['answered_at']
        constraints = [
            models.UniqueConstraint(fields=['player', 'question'], name='unique_answer_per_player_question'),
        ]

    def __str__(self):
        return f'{self.player.nickname} -> pregunta {self.question_id}'
