from django import forms


class ImportQuestionsForm(forms.Form):
    question_set_name = forms.CharField(
        label='Nombre del banco de preguntas',
        max_length=150,
        help_text='Si ya existe un banco con este nombre, las preguntas se agregan ahi. Si no, se crea uno nuevo.',
    )
    question_set_description = forms.CharField(
        label='Descripción (opcional, solo se usa al crear el banco)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )
    file = forms.FileField(
        label='Archivo CSV o Excel',
        help_text=(
            'Columnas requeridas, en este orden: id, categoria, nivel, tags, pregunta, '
            'opcion_a, opcion_b, opcion_c, opcion_d, respuesta_correcta, explicacion, cita_biblica.'
        ),
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise forms.ValidationError('El archivo debe ser .csv, .xlsx o .xls')
        return file
