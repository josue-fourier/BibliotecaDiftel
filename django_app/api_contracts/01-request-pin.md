# API Contract: Request PIN

**Endpoint**: `POST /buzon/api/request-pin`

**Description**: 
Recibe el correo electrónico institucional del estudiante, genera un PIN de 6 dígitos (OTP) en el backend, lo asocia a esa sesión/correo y envía un email con el código a través de SMTP.

## Request

**Headers**:
- `Content-Type: application/json`

**Body**:
```json
{
  "email": "juan.perez@sansano.usm.cl"
}
```

## Responses

### 200 OK (Success)
El correo es válido y el PIN fue enviado.

```json
{
  "message": "PIN enviado correctamente. Revisa tu correo."
}
```

### 400 Bad Request (Invalid Email)
El correo no cumple con los dominios permitidos o está mal formado.

```json
{
  "detail": "El correo debe pertenecer a los dominios @usm.cl o @sansano.usm.cl"
}
```

### 429 Too Many Requests (Rate Limit / Anti-Spam)
El usuario está intentando solicitar demasiados correos en un corto periodo de tiempo.

```json
{
  "detail": "Demasiados intentos. Por favor espera 2 minutos antes de solicitar otro PIN."
}
```
