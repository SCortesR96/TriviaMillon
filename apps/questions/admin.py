from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from .forms import ImportQuestionsForm
from .models import AnswerOption, Category, Question, QuestionSet
from .services.import_questions import ImportQuestionsFromFile, InvalidImportFile

_PROBLEM_PREVIEW_LIMIT = 20


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
    change_list_template = 'admin/questions/questionset/change_list.html'

    @admin.display(description='preguntas')
    def question_count(self, obj):
        return obj.questions.count()

    def get_urls(self):
        custom_urls = [
            path(
                'import-csv/',
                self.admin_site.admin_view(self.import_csv_view),
                name='questions_questionset_import_csv',
            ),
        ]
        return custom_urls + super().get_urls()

    def import_csv_view(self, request):
        """Sube un CSV/Excel y crea (o alimenta) un QuestionSet completo desde el navegador."""
        if request.method == 'POST':
            form = ImportQuestionsForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    result = ImportQuestionsFromFile().execute(
                        request.FILES['file'],
                        form.cleaned_data['question_set_name'],
                        form.cleaned_data['question_set_description'],
                    )
                except InvalidImportFile as exc:
                    messages.error(request, str(exc))
                else:
                    messages.success(
                        request,
                        f'Banco "{result.question_set.name}": {result.created} preguntas creadas, '
                        f'{len(result.problems)} omitidas de {result.total_rows} filas leidas.',
                    )
                    for problem in result.problems[:_PROBLEM_PREVIEW_LIMIT]:
                        messages.warning(
                            request,
                            f'Fila {problem.row} (id={problem.source_id or "?"}): {problem.reason} '
                            f'-- {problem.text[:60]}',
                        )
                    if len(result.problems) > _PROBLEM_PREVIEW_LIMIT:
                        messages.warning(
                            request, f'... y {len(result.problems) - _PROBLEM_PREVIEW_LIMIT} filas mas omitidas.',
                        )
                    return redirect('..')
        else:
            form = ImportQuestionsForm()

        return render(request, 'admin/questions/questionset/import_csv.html', {
            'form': form,
            'opts': self.model._meta,
            'title': 'Importar preguntas desde CSV/Excel',
        })


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'question_set', 'category', 'difficulty', 'order']
    list_filter = ['question_set', 'category', 'difficulty']
    search_fields = ['text', 'tags']
    inlines = [AnswerOptionInline]
