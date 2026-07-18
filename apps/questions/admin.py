from django.contrib import admin

from .models import AnswerOption, Category, Question, QuestionSet


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 0
    min_num = 2


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['name', 'question_count']

    @admin.display(description='preguntas')
    def question_count(self, obj):
        return obj.questions.count()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'question_set', 'category', 'difficulty', 'order']
    list_filter = ['question_set', 'category', 'difficulty']
    search_fields = ['text', 'tags']
    inlines = [AnswerOptionInline]
