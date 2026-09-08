import subprocess
import re
import os
import shutil

def clean_name(name):
    name = name.title()
    replacements = {
        " Ii": " II", " Iii": " III", " Iv": " IV", " V": " V", " Vi": " VI", " I": " I",
        " De ": " de ", " La ": " la ", " Y ": " y ", " En ": " en ", " A ": " a ", " E ": " e ",
        " Del ": " del ", " Para ": " para ", " O ": " o ", " U ": " u "
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    return name.strip()

def process_pdf(pdf_path, title):
    txt = subprocess.check_output(['pdftotext', '-layout', pdf_path, '-']).decode('utf-8')
    lines = txt.split('\n')
    
    sem_re = re.compile(r'^(\d+)°\s+Semestre')
    malla_md = f"---\ntitle: {title}\n---\n# 🗺️ {title}\n\nEste es el índice de ramos ordenado por semestre. Haz clic en cualquier asignatura para ver sus apuntes y recursos.\n\n"
    
    current_semester = ""
    courses = []
    seen = set()
    
    for line in lines:
        line = line.strip()
        sem_match = sem_re.search(line)
        if sem_match:
            current_semester = sem_match.group(1)
            malla_md += f"## Semestre {current_semester}\n"
            continue
            
        if not current_semester: continue
        if ' + ' in line or ' ó ' in line: continue
            
        tokens = line.split()
        if not tokens: continue
        
        sigla = ""
        start_idx = 1
        if re.match(r'^[A-Z]{3}\w*$', tokens[0]):
            sigla = tokens[0]
            if len(tokens) > 1 and re.match(r'^\d+$|^[A-Z0-9]+$', tokens[1]) and len(tokens[1]) <= 3 and sigla in ['HRW', 'TEL', 'DEW', 'HCW', 'ICS', 'IWG', 'HMN']:
                sigla += " " + tokens[1]
                start_idx = 2
        
        if not sigla or sigla == "Sigla": continue
            
        name_tokens = []
        for t in tokens[start_idx:]:
            if re.match(r'^\d$', t): break
            if t in ['DEFIDER', 'FÍSICA', 'MATEMÁTICA', 'ELECTRÓNICA', 'INFORMÁTICA', 'QUÍMICA', 'INDUSTRIAS', 'ESTUDIOS', 'HUMANÍSTICOS', 'DIRECCION', 'GENERAL', 'DOCENCIA', 'INGENIERÍA', 'COMERCIAL']: break
            name_tokens.append(t)
            
        nombre = " ".join(name_tokens)
        if sigla == "TEL132": nombre = "LABORATORIO DE ELECTRÓNICA DIGITAL"
        if sigla == "ELO212": nombre = "LAB. SISTEMAS DIGITALES"
        nombre = nombre.replace("Nuevo programa", "").strip()
        
        if nombre and nombre != "Asignatura":
            clean_nom = clean_name(nombre)
            # NO BRACKETS IN FILENAME
            file_name = f"{sigla} {clean_nom}"
            
            if sigla not in seen:
                malla_md += f"- [[{file_name}]]\n"
                seen.add(sigla)
                courses.append((sigla, clean_nom, file_name))
                
    return malla_md, courses

def main():
    content_dir = "quartz_app/content"
    for d in os.listdir(content_dir):
        if d != "index.md" and d != ".obsidian":
            path = os.path.join(content_dir, d)
            if os.path.isdir(path): shutil.rmtree(path, ignore_errors=True)
            else: os.remove(path)
            
    mallas_dir = os.path.join(content_dir, "Mallas")
    ramos_dir = os.path.join(content_dir, "Ramos")
    
    os.makedirs(mallas_dir, exist_ok=True)
    os.makedirs(ramos_dir, exist_ok=True)
    
    antigua_md, ant_courses = process_pdf("Telemática Malla Antigua.pdf", "Malla Antigua")
    with open(f"{mallas_dir}/Malla Antigua.md", "w") as f: f.write(antigua_md)
        
    nueva_md, nue_courses = process_pdf("Telemática Malla Nueva.pdf", "Malla Nueva")
    with open(f"{mallas_dir}/Malla Nueva.md", "w") as f: f.write(nueva_md)
        
    all_courses = {c[2]: c for c in (ant_courses + nue_courses)}
    
    for file_name, (sigla, nombre, _) in all_courses.items():
        file_path = os.path.join(ramos_dir, f"{file_name}.md")
        content = f"---\ntitle: \"{file_name}\"\n---\n# {file_name}\n\nEste es el repositorio central para la asignatura de {nombre}. Aquí encontrarás apuntes, guías y material de estudio aportado por la comunidad.\n\n---\n\n### 📝 Resúmenes y Apuntes\n*(Aún no hay apuntes subidos. ¡Sé el primero en aportar a través del [Buzón](http://127.0.0.1:8080/buzon/)!)*\n\n### 📝 Certámenes Pasados\n*(Espacio para pautas y certámenes anteriores)*\n"
        with open(file_path, "w") as f: f.write(content)

    index_path = os.path.join(content_dir, "index.md")
    index_content = """---
title: Biblioteca Diftel
---
# 👋 Bienvenidos a la Biblioteca Diftel

La **Biblioteca Diftel** es el repositorio colaborativo de apuntes, guías y certámenes de los estudiantes de Ingeniería Civil Telemática de la USM. Este espacio es mantenido por y para la comunidad, agrupando material académico validado y libre de virus.

## 🗺️ Mallas Curriculares
Para navegar por las asignaturas, puedes explorar los índices por semestre de acuerdo a tu malla curricular:

- [[Malla Nueva]]
- [[Malla Antigua]]

> [!tip] Aporta al Repositorio
> Si tienes resúmenes o certámenes pasados, puedes subirlos a través de nuestro [Buzón Seguro](http://127.0.0.1:8080/buzon/). Una vez que tu aporte sea escaneado por nuestro antivirus, será categorizado y añadido a la bóveda por el equipo de DIFTEL.
"""
    with open(index_path, "w") as f: f.write(index_content)

if __name__ == "__main__": main()
