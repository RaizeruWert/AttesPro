from django.conf import settings
from django.db import models
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    middle_name = models.CharField("Отчество", max_length=120, blank=True)
    phone = models.CharField("Телефон", max_length=40, blank=True)
    institution = models.CharField("Организация образования", max_length=240, blank=True)
    education = models.CharField("Образование", max_length=240, blank=True)
    experience_years = models.PositiveSmallIntegerField("Педагогический стаж, лет", default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name}".strip() or self.user.username

class Assignment(models.Model):
    MANAGEMENT = "management"
    PEDAGOGICAL = "pedagogical"
    MIXED = "mixed"
    KIND_CHOICES = [(MANAGEMENT, "Руководящая"), (PEDAGOGICAL, "Педагогическая"), (MIXED, "Иная / совмещённая")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments")
    kind = models.CharField("Тип деятельности", max_length=20, choices=KIND_CHOICES)
    position = models.CharField("Должность", max_length=180)
    subject = models.CharField("Предмет / направление", max_length=180, blank=True)
    institution = models.CharField("Организация", max_length=240, blank=True)
    workload = models.CharField("Нагрузка / примечание", max_length=120, blank=True)
    start_date = models.DateField("Дата начала работы", null=True, blank=True)
    is_primary = models.BooleanField("Основная должность", default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-is_primary", "position", "subject"]

    def __str__(self):
        suffix = f" — {self.subject}" if self.subject else ""
        return f"{self.position}{suffix}"

class AttestationApplication(models.Model):
    GOAL_CHOICES = [
        ("category", "Присвоение квалификационной категории"),
        ("compliance", "Подтверждение соответствия занимаемой должности"),
        ("consultation", "Предварительная подготовка / консультация"),
    ]
    CATEGORY_CHOICES = [
        ("second", "Вторая"), ("first", "Первая"), ("highest", "Высшая"),
        ("not_selected", "Пока не выбрана"),
    ]
    STATUS_CHOICES = [
        ("draft", "Черновик"), ("collecting", "Сбор документов"),
        ("ready", "Пакет подготовлен"), ("exported", "Архив сформирован"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, related_name="applications")
    goal = models.CharField("Цель", max_length=24, choices=GOAL_CHOICES, default="category")
    category = models.CharField("Категория", max_length=20, choices=CATEGORY_CHOICES, default="not_selected")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="draft")
    answers = models.JSONField("Ответы анкеты", default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Заявка #{self.pk} — {self.assignment}"

class ChecklistItem(models.Model):
    MANAGEMENT = "management"
    PEDAGOGICAL = "pedagogical"
    COMMON = "common"
    SCOPE_CHOICES = [(COMMON, "Для всех"), (MANAGEMENT, "Для руководящих должностей"), (PEDAGOGICAL, "Для педагогических должностей")]
    title = models.CharField("Документ / материал", max_length=240)
    description = models.TextField("Пояснение", blank=True)
    scope = models.CharField("Для какого направления", max_length=20, choices=SCOPE_CHOICES, default=COMMON)
    required = models.BooleanField("Обязательный по настройке проекта", default=True)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

class EvidenceDocument(models.Model):
    application = models.ForeignKey(AttestationApplication, on_delete=models.CASCADE, related_name="documents")
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploads")
    title = models.CharField("Название документа", max_length=240)
    file = models.FileField("Файл", upload_to="evidence/%Y/%m/")
    note = models.CharField("Комментарий", max_length=500, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
