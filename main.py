import streamlit as st
import random
import re
import os
from pypdf import PdfReader

# --- 1. CONFIGURARE FIȘIERE PDF ---
# Aici adaugi numele capitolelor și fișierele PDF corespunzătoare
PDF_FILES = {
    "Capitolul 5: Piața financiară": "GRILE MACRO CAP 5.pdf",
    "Capitolul 6: (Nume capitol 6)": "GRILE_MACRO_CAP_6.pdf", # Înlocuiește cu numele real
    # "Capitolul 7": "fisier_cap_7.pdf",
    # "Capitolul 8": "fisier_cap_8.pdf"
}

# --- 2. PARSAREA PDF-ULUI ---
def parse_pdf_quiz(file_path):
    """
    Citește PDF-ul și extrage întrebările.
    Se bazează pe faptul că opțiunile încep cu a), b), c) sau @a).
    Tot textul de dinaintea opțiunilor devine corpul întrebării.
    """
    if not os.path.exists(file_path):
        return []

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Eroare la citirea PDF: {e}")
        return []

    lines = text.split('\n')
    questions = []
    
    current_q_text = []
    current_options = []
    correct_indices = []
    
    # Caută linii care încep cu a), @a), B), @c) etc.
    opt_pattern = re.compile(r'^(@?)([a-zA-Z])\)\s*(.+)')

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Ignorăm titlurile de pagini dacă e cazul (ex: "Capitolul 5: Piaţa financiară")
        if line.lower().startswith("capitolul"):
            continue

        opt_match = opt_pattern.match(line)
        
        if opt_match:
            # Am găsit o opțiune de răspuns
            is_correct = bool(opt_match.group(1) == '@')
            opt_text = opt_match.group(3)
            
            # Verificăm dacă '@' a rămas ascuns în interiorul textului (din erori de formatare)
            if '@' in opt_text:
                is_correct = True
                opt_text = opt_text.replace('@', '').strip()
            
            current_options.append(opt_text)
            if is_correct:
                correct_indices.append(len(current_options) - 1)
        else:
            # Nu este o opțiune. 
            # Dacă aveam deja opțiuni salvate, înseamnă că am dat de o ÎNTREBARE NOUĂ.
            if current_options:
                questions.append({
                    "text": " ".join(current_q_text).strip(),
                    "options": current_options,
                    "correct_indices": correct_indices
                })
                # Resetăm variabilele pentru noua întrebare
                current_q_text = [line]
                current_options = []
                correct_indices = []
            else:
                # Suntem încă în procesul de citire al enunțului întrebării curente
                current_q_text.append(line)
                
    # Adăugăm și ultima întrebare rămasă în memorie la finalul fișierului
    if current_q_text and current_options:
        questions.append({
            "text": " ".join(current_q_text).strip(),
            "options": current_options,
            "correct_indices": correct_indices
        })

    return questions

# --- 3. FUNCȚII AUXILIARE ---
def restart_quiz():
    """Resetează progresul testului curent."""
    st.session_state.session_id += 1
    st.session_state.verified_questions = set()
    st.session_state.correct_answers = set()
    if 'questions' in st.session_state and st.session_state.questions:
        random.shuffle(st.session_state.questions)

def change_chapter():
    """Schimbă PDF-ul și resetează testul."""
    # Stergem intrebarile vechi pentru a forta reincarcarea
    if 'questions' in st.session_state:
        del st.session_state['questions']
    restart_quiz()

# --- 4. INTERFAȚA PRINCIPALĂ ---
def main():
    st.set_page_config(page_title="Quiz Macroeconomie", page_icon="📈", layout="wide")
    
    # --- SELECTORUL DE CAPITOLE (SIDEBAR) ---
    with st.sidebar:
        st.header("📂 Alege Capitolul")
        selected_chapter = st.selectbox(
            "Selectează PDF-ul din care vrei să dai testul:",
            list(PDF_FILES.keys()),
            on_change=change_chapter,
            key="chapter_selector"
        )
        
        st.markdown("---")
        
    st.title(f"📈 Test Grilă: {selected_chapter}")

    # Inițializări Session State
    if 'questions' not in st.session_state:
        current_file = PDF_FILES[selected_chapter]
        raw_questions = parse_pdf_quiz(current_file)
        
        if raw_questions:
            random.shuffle(raw_questions)
            st.session_state.questions = raw_questions
        else:
            st.warning(f"Nu s-au găsit întrebări sau fișierul '{current_file}' lipsește. Te rog asigură-te că PDF-ul este în același folder cu scriptul.")
            st.stop()
            
    if 'session_id' not in st.session_state:
        st.session_state.session_id = 0
    if 'verified_questions' not in st.session_state:
        st.session_state.verified_questions = set()
    if 'correct_answers' not in st.session_state:
        st.session_state.correct_answers = set()

    sid = st.session_state.session_id
    total_questions = len(st.session_state.questions)
    verified_count = len(st.session_state.verified_questions)
    current_score = len(st.session_state.correct_answers)

    # --- STATISTICI LIVE (SIDEBAR) ---
    with st.sidebar:
        st.header("📊 Progres")
        if total_questions > 0:
            progres = verified_count / total_questions
            st.progress(progres)
            st.write(f"Întrebări completate: **{verified_count} / {total_questions}**")
            st.write(f"Răspunsuri corecte: **{current_score}**")
            
            if verified_count > 0:
                acc = (current_score / verified_count) * 100
                st.metric("Acuratețe momentană", f"{acc:.1f}%")
        
        st.markdown("---")
        st.button("🔄 Restart Test", on_click=restart_quiz)

    # --- AFIȘAREA LISTEI DE ÎNTREBĂRI ---
    for i, q in enumerate(st.session_state.questions):
        
        with st.container():
            st.markdown(f"#### {i+1}. {q['text']}")
            
            selected_indices = []
            
            # Afișăm opțiunile
            for idx, opt in enumerate(q['options']):
                # Eliminăm orice literă din fata (ex: "a) ") pentru a face UI-ul mai curat, dacă vrei
                # opt_clean = re.sub(r'^[a-zA-Z]\)\s*', '', opt)
                chk_key = f"chk_{sid}_{i}_{idx}"
                is_disabled = i in st.session_state.verified_questions
                
                checked = st.checkbox(opt, key=chk_key, disabled=is_disabled)
                if checked:
                    selected_indices.append(idx)

            # --- BUTONUL DE VERIFICARE ---
            if i not in st.session_state.verified_questions:
                if st.button(f"Verifică întrebarea {i+1}", key=f"btn_check_{sid}_{i}"):
                    st.session_state.verified_questions.add(i)
                    
                    if q['correct_indices']:
                        if sorted(selected_indices) == sorted(q['correct_indices']):
                            st.session_state.correct_answers.add(i)
                    
                    st.rerun()
            
            # --- AFIȘAREA REZULTATULUI IMEDIAT ---
            if i in st.session_state.verified_questions:
                correct_indices = q['correct_indices']
                
                if not correct_indices:
                    st.warning("⚠️ Această întrebare nu are răspunsul marcat în PDF (lipsește @).")
                else:
                    if sorted(selected_indices) == sorted(correct_indices):
                        st.success("✅ Corect!")
                    else:
                        correct_texts = [q['options'][idx] for idx in correct_indices]
                        st.error("❌ Greșit.")
                        st.info(f"**Răspuns corect:** {', '.join(correct_texts)}")
            
            st.markdown("---")

    # --- ZONA DE SCOR FINAL ---
    if verified_count == total_questions and total_questions > 0:
        
        valid_total = sum(1 for q in st.session_state.questions if q['correct_indices'])
        final_percentage = (current_score / valid_total) * 100 if valid_total > 0 else 0

        st.markdown("""
        <div style="background-color:#d4edda;padding:20px;border-radius:10px;border:2px solid #c3e6cb">
            <h2 style="color:#155724;text-align:center;">🏆 TEST COMPLETAT!</h2>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Scor Final", f"{current_score} / {valid_total}")
        col2.metric("Procentaj", f"{final_percentage:.2f}%")
        
        if final_percentage >= 50:
            st.balloons()
            col3.success("AI PROMOVAT!")
        else:
            col3.error("MAI ÎNCEARCĂ...")

if __name__ == "__main__":
    main()
