from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class QuestionSet(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Question(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = 'principiante', 'Principiante'
        INTERMEDIATE = 'intermedio', 'Intermedio'
        ADVANCED = 'avanzado', 'Avanzado'
        EXPERT = 'experto', 'Experto'

    question_set = models.ForeignKey(QuestionSet, on_delete=models.CASCADE, related_name='questions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    text = models.TextField()
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    order = models.PositiveIntegerField(null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True)
    explanation = models.TextField(blank=True)
    reference = models.CharField(max_length=255, blank=True)
    source_id = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['question_set', 'order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['question_set', 'source_id'],
                condition=~models.Q(source_id=''),
                name='unique_source_id_per_set',
            ),
        ]

    def __str__(self):
        return self.text[:80]


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['question', 'order']

    def __str__(self):
        return f'{self.text} ({"correcta" if self.is_correct else "incorrecta"})'
