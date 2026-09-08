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
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import USMUser

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
        for filename in os.listdir(recursos_dir):
            filepath = os.path.join(recursos_dir, filename)
            if os.path.isfile(filepath):
                # Omitir archivos ocultos
                if filename.startswith('.'):
                    continue
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
                
                files_list.append({
                    "name": filename,
                    "url": f"/recursos/{filename}",
                    "size": size_str,
                    "date": date_str
                })
                
    files_list.sort(key=lambda x: x["date"], reverse=True)
    cache.set("recursos_list", files_list, 300) # Caché por 5 minutos
    
    return JsonResponse({"files": files_list})
