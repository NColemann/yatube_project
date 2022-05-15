from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма создания поста."""
    class Meta:
        model = Post

        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст поста'),
            'group': ('Группа'),
        }
        help_texts = {
            'text': ('Здесь должен быть текст поста.'),
            'group': ('Выберете группу.'),
        }

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Поле не должно быть пустым')

        return data


class CommentForm(forms.ModelForm):
    """Форма добавления комментария."""
    class Meta:
        model = Comment

        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Поле не должно быть пустым')

        return data
