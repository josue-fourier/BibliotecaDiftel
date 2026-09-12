import json
import os
import re
import time
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from multiprocessing import Value
from random import randrange

from decouple import config
from django.core.cache import cache
from django.core.mail import send_mail  # For email sending
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import USMUser, InitialProject, Workshop, EVENT_TYPE_CHOICES, CommunityMember

def initial_projects_view(request):
    generations = InitialProject.objects.values_list('generation', flat=True).distinct().order_by('-generation')
    
    selected_generation = None
    if generations:
        selected_generation = generations[0]
        
    return render(request, 'dashboard/initial_projects.html', {
        'generations': generations,
        'selected_generation': selected_generation
    })

def initial_projects_list_view(request, generation):
    projects = InitialProject.objects.filter(generation=generation).prefetch_related('images')
    return render(request, 'dashboard/partials/initial_projects_list.html', {
        'projects': projects,
        'generation': generation
    })


def _parse_year_param(year_val):
    """Safely parses a year parameter into an integer or None."""
    if not year_val:
        return None
    val_str = str(year_val).strip().lower()
    if val_str in ('all', 'todos', ''):
        return None
    try:
        val = int(val_str)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None


def workshops_view(request, year=None):
    """
    Main view and HTMX partial handler for Talleres Telemáticos.
    - Full request (request.htmx is False): Renders 'dashboard/workshops.html'.
    - HTMX request (request.htmx is True): Renders 'dashboard/partials/workshops_list.html'.
    - Supports year filtering via route kwarg `year` or query param `?year=...`.
    - Supports optional event type filtering via query param `?type=...` or `?event_type=...`.
    """
    # 1. Resolve year filter
    year_param = year if year is not None else request.GET.get('year')
    selected_year = _parse_year_param(year_param)

    # 2. Build base queryset with newest-first ordering and prefetched images
    workshops = Workshop.objects.all().prefetch_related('images').order_by('-year', '-created_at', '-id')

    if selected_year is not None:
        workshops = workshops.filter(year=selected_year)

    # 3. Optional event_type filter
    event_type = request.GET.get('event_type') or request.GET.get('type')
    valid_event_types = dict(EVENT_TYPE_CHOICES)
    if event_type and event_type in valid_event_types:
        workshops = workshops.filter(event_type=event_type)
    else:
        event_type = None

    # 4. Available years (lazy QuerySet; evaluated only if referenced in template)
    years = Workshop.objects.values_list('year', flat=True).distinct().order_by('-year')

    # 5. Build context
    context = {
        'workshops': workshops,
        'years': years,
        'active_year': selected_year,
        'selected_year': selected_year,
        'event_types': EVENT_TYPE_CHOICES,
        'selected_type': event_type,
    }

    # 6. HTMX detection (supports django_htmx middleware, RequestFactory headers, and ?partial=1)
    is_htmx = (
        bool(getattr(request, 'htmx', False))
        or request.headers.get('HX-Request') == 'true'
        or request.GET.get('partial') in ('1', 'true', 'True')
    )

    if is_htmx:
        return render(request, 'dashboard/partials/workshops_list.html', context)
    return render(request, 'dashboard/workshops.html', context)


def workshops_list_view(request, year=None):
    """Explicit endpoint that always renders the partial workshops_list.html."""
    year_param = year if year is not None else request.GET.get('year')
    selected_year = _parse_year_param(year_param)

    workshops = Workshop.objects.all().prefetch_related('images').order_by('-year', '-created_at', '-id')
    if selected_year is not None:
        workshops = workshops.filter(year=selected_year)

    event_type = request.GET.get('event_type') or request.GET.get('type')
    if event_type and event_type in dict(EVENT_TYPE_CHOICES):
        workshops = workshops.filter(event_type=event_type)
    else:
        event_type = None

    years = Workshop.objects.values_list('year', flat=True).distinct().order_by('-year')

    context = {
        'workshops': workshops,
        'years': years,
        'active_year': selected_year,
        'selected_year': selected_year,
        'event_types': EVENT_TYPE_CHOICES,
        'selected_type': event_type,
    }
    return render(request, 'dashboard/partials/workshops_list.html', context)


# -----------------------------------------------------------------------------
# Milestone 3: Comunidad Telemática (Directorio de Alumnos & Egresados)
# -----------------------------------------------------------------------------
def _parse_generation_param(gen_val):
    """Safely parses a generation parameter into an integer or None."""
    if not gen_val:
        return None
    val_str = str(gen_val).strip().lower()
    if val_str in ('all', 'todos', 'todas', ''):
        return None
    try:
        val = int(val_str)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None


def community_view(request, generation=None):
    """
    Main view and HTMX handler for Comunidad Telemática.
    - Full request (request.htmx is False): Renders 'dashboard/community.html'.
    - HTMX request (request.htmx is True): Renders 'dashboard/partials/community_list.html'.
    - Supports generation filtering via route kwarg `generation` or query param `?generation=...`.
    - Supports search query via `?q=...` or `?search=...` (name, current_role, bio).
    """
    # 1. Resolve generation filter
    gen_param = generation if generation is not None else (request.GET.get('generation') or request.GET.get('gen'))
    selected_generation = _parse_generation_param(gen_param)

    # 2. Resolve search query
    search_query = (request.GET.get('q') or request.GET.get('search') or '').strip()

    # 3. Build queryset with model ordering ('-generation', 'name', 'id')
    members = CommunityMember.objects.all()

    if selected_generation is not None:
        members = members.filter(generation=selected_generation)

    if search_query:
        members = members.filter(
            Q(name__icontains=search_query) |
            Q(current_role__icontains=search_query) |
            Q(bio__icontains=search_query)
        )

    # 4. Available generations for filter pills/dropdown
    generations = CommunityMember.objects.values_list('generation', flat=True).distinct().order_by('-generation')

    # 5. Build context
    context = {
        'members': members,
        'generations': generations,
        'selected_generation': selected_generation,
        'active_generation': selected_generation,
        'search_query': search_query,
        'total_count': members.count(),
    }

    # 6. HTMX detection
    is_htmx = (
        bool(getattr(request, 'htmx', False))
        or request.headers.get('HX-Request') == 'true'
        or request.GET.get('partial') in ('1', 'true', 'True')
    )

    if is_htmx:
        return render(request, 'dashboard/partials/community_list.html', context)
    return render(request, 'dashboard/community.html', context)


def community_list_view(request, generation=None):
    """Explicit endpoint that always renders the partial community_list.html."""
    gen_param = generation if generation is not None else (request.GET.get('generation') or request.GET.get('gen'))
    selected_generation = _parse_generation_param(gen_param)
    search_query = (request.GET.get('q') or request.GET.get('search') or '').strip()

    members = CommunityMember.objects.all()
    if selected_generation is not None:
        members = members.filter(generation=selected_generation)

    if search_query:
        members = members.filter(
            Q(name__icontains=search_query) |
            Q(current_role__icontains=search_query) |
            Q(bio__icontains=search_query)
        )

    generations = CommunityMember.objects.values_list('generation', flat=True).distinct().order_by('-generation')

    context = {
        'members': members,
        'generations': generations,
        'selected_generation': selected_generation,
        'active_generation': selected_generation,
        'search_query': search_query,
        'total_count': members.count(),
    }
    return render(request, 'dashboard/partials/community_list.html', context)



LOWER_PIN_BOUND = 100000
UPPER_PIN_BOUND = 999999

EXPIRATION_SPAN_MINUTES = 15

MAX_SIZE_BYTES = 2e9 # 2 Gigabytes

TMP_DIR = "/data/buzon/tmp"

@csrf_exempt
@require_POST
def request_pin(request):
    if request.content_type != "application/json":
        return JsonResponse({"detail": "Faltan parámetros requeridos"}, status=400)

    try:
        data = json.loads(request.body)

        if not isinstance(data,dict):
            return JsonResponse({"detail": "Json inválido."}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({"detail": "Json inválido."}, status=400)
    except UnicodeDecodeError:
         return JsonResponse({"detail": "Error de codificación."}, status=400)

    email = data.get("email")

    if not email or not isinstance(email, str):
        return JsonResponse({"detail": "Json inválido."}, status=400)

    email = email.strip().lower()
    
    if not email.endswith("@usm.cl") and not email.endswith("@sansano.usm.cl"):
        return JsonResponse({"detail": "El correo debe pertenecer a los dominios @usm.cl o @sansano.usm.cl"}, status=400)

    pin = randrange(LOWER_PIN_BOUND, UPPER_PIN_BOUND)

    new_usm_user = USMUser(pin=pin, email=email)
    new_usm_user.save() # Create user whose pin is not expired and has not been checked or validated

    mailer_name = config("EMAIL_MAILER", default="default")

    send_mail(
        "¡Repositorio Telemático!",
        f"Este es tu pin de verificación: {pin}. Tiene 15 minutos de vigencia. Úsalo en el buzón para subir archivos y solicitar su adición.",
        "josue@buzon-diftel.josnic.cl",
        [email,],
        using=mailer_name
    )

    return JsonResponse({"message": "PIN enviado correctamente. Revisa tu correo."}, status=200)


@csrf_exempt
@require_POST
def upload_file(request):
    if not request.content_type or not request.content_type.startswith("multipart/form-data"):
        return JsonResponse({"detail": "Content-Type inválido."}, status=400)

    email = request.POST.get("email","").strip().lower()
    pin_str = request.POST.get("pin","").strip()

    if not email or not pin_str:
        return JsonResponse({"detail": "Faltan parámetros requeridos"}, status=400)

    pin = 0
    try:
        pin = int(pin_str)
    except ValueError:
        return JsonResponse({"detail": "Faltan parámetros requeridos"}, status=400)

    limite_tiempo = now()-timedelta(minutes=EXPIRATION_SPAN_MINUTES)

    usm_user = USMUser.objects.filter(
        pin=pin,
        email=email,
        checked=False,
        timestamp__gte=limite_tiempo
    ).first()

    if not usm_user:
        return JsonResponse({"detail": "Código PIN incorrecto o expirado."}, status=401)

    usm_user.checked=True
    usm_user.save()

    timestamp = usm_user.timestamp
    timedelta_15_min = timestamp+timedelta(minutes=EXPIRATION_SPAN_MINUTES)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"detail": "Faltan parámetros requeridos"}, status=400)

    if not uploaded_file.name:
        return JsonResponse({"detail": "Faltan parámetros requeridos"}, status=400)

    safe_name = sanitize_filename(uploaded_file.name)
    safe_email = sanitize_filename(email.replace('@', '_'))
    unique_safe_name = f"{int(time.time())}_{safe_email}_{safe_name}"
    file_path = os.path.join(TMP_DIR, unique_safe_name)

    if uploaded_file.size > MAX_SIZE_BYTES:
        return JsonResponse({"detail": "Archivo demasiado grande."}, status=413)
    try:
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
    except IOError:
        return JsonResponse({"detail": "Error interno al guardar el archivo"}, status=500)

    return JsonResponse({"detail": "Archivo recibido correctamente. Será analizado en su momento. ¡Muchas gracias!"})



def sanitize_filename(filename):
    filename = os.path.basename(filename)
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    return safe_name

def list_recursos(request):
    cached_data = cache.get("recursos_list")
    if cached_data:
        return JsonResponse({"files": cached_data})
        
    recursos_dir = "/data/recursos"
    files_list = []
    
    if os.path.exists(recursos_dir) and os.path.isdir(recursos_dir):
        for root, dirs, files in os.walk(recursos_dir):
            for filename in files:
                # Omitir archivos ocultos
                if filename.startswith('.'):
                    continue
                
                filepath = os.path.join(root, filename)
                
                size_bytes = os.path.getsize(filepath)
                if size_bytes >= 1e9:
                    size_str = f"{size_bytes / 1e9:.2f} GB"
                elif size_bytes >= 1e6:
                    size_str = f"{size_bytes / 1e6:.2f} MB"
                elif size_bytes >= 1e3:
                    size_str = f"{size_bytes / 1e3:.2f} KB"
                else:
                    size_str = f"{size_bytes} B"
                    
                mod_time = os.path.getmtime(filepath)
                date_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
                
                # Obtener la ruta relativa para el nombre y el link
                rel_path = os.path.relpath(filepath, recursos_dir)
                
                files_list.append({
                    "name": rel_path,
                    "url": f"/recursos/{rel_path}",
                    "size": size_str,
                    "date": date_str
                })
                
    files_list.sort(key=lambda x: x["date"], reverse=True)
    cache.set("recursos_list", files_list, 300) # Caché por 5 minutos
    
    return JsonResponse({"files": files_list})
