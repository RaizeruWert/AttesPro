import io, os, zipfile
from pathlib import Path
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import get_valid_filename
from .models import Profile, Assignment, AttestationApplication, ChecklistItem, EvidenceDocument
from .forms import RegisterForm, ProfileForm, AssignmentForm, ApplicationForm, EvidenceForm, QuestionnaireForm

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/home.html")

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            login(request, user)
            messages.success(request, "Аккаунт создан. Заполните профиль и добавьте должности.")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "core/form.html", {"form": form, "title": "Регистрация"})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("dashboard")
    else:
        form = AuthenticationForm(request)
    return render(request, "core/form.html", {"form": form, "title": "Вход"})

def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("home")

@login_required
def dashboard(request):
    assignments = Assignment.objects.filter(user=request.user)
    applications = AttestationApplication.objects.filter(user=request.user).select_related("assignment")
    return render(request, "core/dashboard.html", {"assignments": assignments, "applications": applications})

@login_required
def profile(request):
    obj, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            request.user.first_name = request.POST.get("first_name", request.user.first_name).strip()
            request.user.last_name = request.POST.get("last_name", request.user.last_name).strip()
            request.user.email = request.POST.get("email", request.user.email).strip()
            request.user.save()
            messages.success(request, "Профиль сохранён.")
            return redirect("dashboard")
    else:
        form = ProfileForm(instance=obj)
    return render(request, "core/profile.html", {"form": form})

@login_required
def assignment_add(request):
    if request.method == "POST":
        form = AssignmentForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, "Должность добавлена. Можно добавить ещё одну — аккаунт останется один.")
            return redirect("dashboard")
    else:
        form = AssignmentForm()
    return render(request, "core/form.html", {"form": form, "title": "Добавить должность / предмет"})

@login_required
def application_add(request):
    if not Assignment.objects.filter(user=request.user).exists():
        messages.warning(request, "Сначала добавьте хотя бы одну должность.")
        return redirect("assignment_add")
    if request.method == "POST":
        form = ApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.save()
            messages.success(request, "Заявка создана для выбранной должности.")
            return redirect("application_detail", pk=app.pk)
    else:
        form = ApplicationForm(user=request.user)
    return render(request, "core/form.html", {"form": form, "title": "Новая подготовка к аттестации"})

def _owned_application(request, pk):
    app = get_object_or_404(AttestationApplication.objects.select_related("assignment"), pk=pk, user=request.user)
    return app

def _checklist_for(app):
    kind = app.assignment.kind
    scopes = [ChecklistItem.COMMON]
    if kind == Assignment.MANAGEMENT:
        scopes.append(ChecklistItem.MANAGEMENT)
    elif kind == Assignment.PEDAGOGICAL:
        scopes.append(ChecklistItem.PEDAGOGICAL)
    else:
        scopes.extend([ChecklistItem.MANAGEMENT, ChecklistItem.PEDAGOGICAL])
    return ChecklistItem.objects.filter(active=True, scope__in=scopes)

@login_required
def application_detail(request, pk):
    app = _owned_application(request, pk)
    items = list(_checklist_for(app))
    docs = list(app.documents.select_related("checklist_item"))
    attached_ids = {d.checklist_item_id for d in docs if d.checklist_item_id}
    missing = [i for i in items if i.required and i.id not in attached_ids]
    if missing and app.status in ("ready", "exported"):
        app.status = "collecting"
        app.save(update_fields=["status", "updated_at"])
    return render(request, "core/application_detail.html", {
        "app": app, "items": items, "documents": docs, "missing": missing,
        "questionnaire_fields": app.answers,
    })

@login_required
def questionnaire(request, pk):
    app = _owned_application(request, pk)
    form = QuestionnaireForm(request.POST or None, initial=app.answers, assignment_kind=app.assignment.kind)
    # Add assignment-specific context: pedagogical and management sections are shown conditionally.
    if request.method == "POST" and form.is_valid():
        app.answers = form.cleaned_data
        app.save()
        messages.success(request, "Анкета сохранена.")
        return redirect("application_detail", pk=app.pk)
    return render(request, "core/form.html", {
        "form": form, "title": "Анкета аттестации",
        "subtitle": f"Анкета относится к должности: {app.assignment}",
        "show_management": app.assignment.kind in (Assignment.MANAGEMENT, Assignment.MIXED),
        "show_pedagogical": app.assignment.kind in (Assignment.PEDAGOGICAL, Assignment.MIXED),
    })

@login_required
def document_add(request, pk):
    app = _owned_application(request, pk)
    if request.method == "POST":
        form = EvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.application = app
            doc.save()
            if app.status == "draft":
                app.status = "collecting"
                app.save(update_fields=["status", "updated_at"])
            messages.success(request, "Документ добавлен.")
            return redirect("application_detail", pk=app.pk)
    else:
        form = EvidenceForm()
        form.fields["checklist_item"].queryset = _checklist_for(app)
    return render(request, "core/form.html", {"form": form, "title": "Загрузить подтверждающий документ"})

@login_required
def document_download(request, pk):
    doc = get_object_or_404(EvidenceDocument, pk=pk, application__user=request.user)
    if not doc.file:
        raise Http404()
    return FileResponse(doc.file.open("rb"), as_attachment=True, filename=Path(doc.file.name).name)

@login_required
def export_zip(request, pk):
    app = _owned_application(request, pk)
    items = list(_checklist_for(app))
    docs = list(app.documents.select_related("checklist_item"))
    attached_ids = {d.checklist_item_id for d in docs if d.checklist_item_id}
    missing = [i for i in items if i.required and i.id not in attached_ids]
    if missing:
        messages.error(request, "Архив не сформирован: сначала проверьте недостающие обязательные материалы.")
        return redirect("application_detail", pk=app.pk)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        profile = getattr(request.user, "profile", None)
        summary = [
            "АТТЕСТПРО — ПАКЕТ МАТЕРИАЛОВ",
            f"Педагог: {request.user.last_name} {request.user.first_name}",
            f"Должность: {app.assignment.position}",
            f"Предмет / направление: {app.assignment.subject or 'не указано'}",
            f"Организация: {app.assignment.institution or (profile.institution if profile else '')}",
            f"Цель: {app.get_goal_display()}",
            f"Категория: {app.get_category_display()}",
            f"Дата формирования: {app.updated_at:%d.%m.%Y}",
            "",
            "АНКЕТА",
        ]
        for key, value in app.answers.items():
            summary.append(f"{key}: {value}")
        summary += ["", "ПРИЛОЖЕННЫЕ ДОКУМЕНТЫ"]
        for doc in docs:
            summary.append(f"- {doc.title}" + (f" ({doc.checklist_item.title})" if doc.checklist_item else ""))
            if doc.file and os.path.exists(doc.file.path):
                safe = get_valid_filename(Path(doc.file.name).name)
                zf.write(doc.file.path, f"Документы/{safe}")
        zf.writestr("Сопроводительная_информация.txt", "\n".join(summary))
        zf.writestr("ПРОВЕРКА_ПЕРЕД_ПОДАЧЕЙ.txt",
            "Этот архив сформирован информационной системой АттестПро для предварительной подготовки материалов.\n"
            "Он не является официальным решением аттестационной комиссии и не подтверждает присвоение категории.\n"
            "Перед подачей проверьте актуальные требования и формы в Министерстве просвещения ПМР.")
    app.status = "exported"
    app.save(update_fields=["status", "updated_at"])
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="AttestPro_application_{app.pk}.zip"'
    return response
