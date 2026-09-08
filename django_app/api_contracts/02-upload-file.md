# API Contract: Upload File

**Endpoint**: `POST /buzon/api/upload`

**Description**: 
Recibe el archivo a subir junto con el PIN de verificación y el correo. Valida que el PIN sea correcto para ese correo, guarda el archivo en el directorio temporal (`/data/buzon/tmp/`) y retorna éxito.

## Request

**Headers**:
- `Content-Type: multipart/form-data`

**Body Fields (FormData)**:
- `email` (string): El correo electrónico del usuario.
- `pin` (string): El código de 6 dígitos.
- `file` (binary): El archivo a subir.

## Responses

### 200 OK (Success)
El PIN es correcto y el archivo fue guardado en `/data/buzon/tmp/`.

```json
{
  "message": "Archivo recibido correctamente. Ha sido enviado a la cola de escaneo de seguridad."
}
```

### 401 Unauthorized (Invalid PIN)
El PIN provisto no coincide o expiró.

```json
{
  "detail": "Código PIN incorrecto o expirado."
}
```

### 400 Bad Request (Missing parameters)
Falta el archivo, el correo o el PIN.

```json
{
  "detail": "Faltan parámetros requeridos (file, email, pin)."
}
```

### 413 Payload Too Large
Manejado automáticamente por Nginx (o Django) si el archivo excede los límites configurados.

```html
<html><body><h1>413 Request Entity Too Large</h1></body></html>
```
