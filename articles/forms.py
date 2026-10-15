from django import forms

from .models import Comment, TopicSuggestion


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Напишите комментарий'})}


class TopicSuggestionForm(forms.ModelForm):
    class Meta:
        model = TopicSuggestion
        fields = ('title', 'description')
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}


class ModeratorCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'status', 'moderator_note')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'moderator_note': forms.TextInput(attrs={'placeholder': 'Причина или пояснение'}),
        }


class ModeratorSuggestionForm(forms.ModelForm):
    class Meta:
        model = TopicSuggestion
        fields = ('status', 'moderator_note')
        widgets = {
            'moderator_note': forms.TextInput(attrs={'placeholder': 'Ответ пользователю'}),
        }
