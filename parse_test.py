import subprocess
import re

def process_pdf(pdf_path):
    txt = subprocess.check_output(['pdftotext', '-layout', pdf_path, '-']).decode('utf-8')
    lines = txt.split('\n')
    
    sem_re = re.compile(r'^(\d+)°\s+Semestre')
    course_re = re.compile(r'^([A-Z]{3}\s*[A-Z0-9]+)\s+([A-ZÁÉÍÓÚÑ][^\d]+?)\s{2,}')
    
    current_semester = ""
    
    for line in lines:
        line = line.strip()
        sem_match = sem_re.search(line)
        if sem_match:
            current_semester = sem_match.group(1)
            print(f"--- SEMESTER {current_semester} ---")
            continue
            
        if not current_semester:
            continue
            
        # Instead of strict regex, let's just use string manipulation
        # Sigla is the first 1 or 2 tokens.
        tokens = line.split()
        if not tokens: continue
        
        # Check if first token is a valid sigla (e.g., FIS100, MAT021, TEL)
        if re.match(r'^[A-Z]{3}\w*$', tokens[0]):
            sigla = tokens[0]
            start_idx = 1
            if len(tokens) > 1 and re.match(r'^\d+$|^[A-Z0-9]+$', tokens[1]) and len(tokens[1]) <= 3 and sigla in ['HRW', 'TEL', 'DEW', 'HCW']:
                sigla += " " + tokens[1]
                start_idx = 2
                
            # Now the name is the tokens until we hit a solitary number or a known department
            name_tokens = []
            for t in tokens[start_idx:]:
                if re.match(r'^\d$', t): # Single digit (hours)
                    break
                if t in ['DEFIDER', 'FÍSICA', 'MATEMÁTICA', 'ELECTRÓNICA', 'INFORMÁTICA', 'QUÍMICA', 'INDUSTRIAS']:
                    break
                name_tokens.append(t)
            
            nombre = " ".join(name_tokens)
            if nombre and nombre != "Asignatura":
                print(f"[{sigla}] {nombre}")

process_pdf("Telemática Malla Antigua.pdf")
