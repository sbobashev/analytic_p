from django import forms
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    # Конструктор класса, который вызывается при создании формы
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Перебираем все поля формы
        for field_name, field in self.fields.items():
            # Добавляем CSS-класс к каждому полю для стилизации
            field.widget.attrs['class'] = 'form-control'
            # Устанавливаем placeholder, равный названию поля
            field.widget.attrs['placeholder'] = field.label

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)
