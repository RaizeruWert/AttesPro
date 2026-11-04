from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Assignment, AttestationApplication, EvidenceDocument

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=150)
    last_name = forms.CharField(label="Фамилия", max_length=150)
    email = forms.EmailField(label="Электронная почта")
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Логин"
        self.fields["password1"].label = "Пароль"
        self.fields["password2"].label = "Повторите пароль"

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["middle_name", "phone", "institution", "education", "experience_years"]

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["kind", "position", "subject", "institution", "workload", "start_date", "is_primary"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"})}
    def clean(self):
        data = super().clean()
        if data.get("kind") == Assignment.PEDAGOGICAL and not data.get("subject"):
            self.add_error("subject", "Для педагогической должности укажите предмет или направление.")
        return data

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = AttestationApplication
        fields = ["assignment", "goal", "category"]
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["assignment"].queryset = Assignment.objects.filter(user=user)

class EvidenceForm(forms.ModelForm):
    class Meta:
        model = EvidenceDocument
        fields = ["checklist_item", "title", "file", "note"]
        widgets = {"note": forms.TextInput(attrs={"placeholder": "Необязательный комментарий"})}
    def clean_file(self):
        f = self.cleaned_data["file"]
        allowed = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".odt"}
        import os
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in allowed:
            raise forms.ValidationError("Разрешены PDF, Office-документы и изображения.")
        if f.size > 15 * 1024 * 1024:
            raise forms.ValidationError("Размер файла не должен превышать 15 МБ.")
        return f

class QuestionnaireForm(forms.Form):
    institution_name = forms.CharField(label="Полное название организации", required=False)
    years_in_position = forms.IntegerField(label="Стаж в выбранной должности (лет)", min_value=0, required=False)
    professional_development = forms.CharField(label="Повышение квалификации за последние годы", widget=forms.Textarea, required=False)
    achievements = forms.CharField(label="Профессиональные достижения", widget=forms.Textarea, required=False)
    self_analysis = forms.CharField(label="Самоанализ профессиональной деятельности", widget=forms.Textarea, required=False)
    teaching_methods = forms.CharField(label="Методы и технологии преподавания", widget=forms.Textarea, required=False)
    management_results = forms.CharField(label="Результаты управленческой деятельности", widget=forms.Textarea, required=False)
    team_development = forms.CharField(label="Работа с педагогическим коллективом", widget=forms.Textarea, required=False)

    def __init__(self, *args, assignment_kind=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Вопросы формируются по конкретной должности, а не по всему профилю сразу.
        if assignment_kind == "management":
            self.fields.pop("teaching_methods", None)
        elif assignment_kind == "pedagogical":
            self.fields.pop("management_results", None)
            self.fields.pop("team_development", None)
