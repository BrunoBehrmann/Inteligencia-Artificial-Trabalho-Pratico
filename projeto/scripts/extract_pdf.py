import sys
import os
import subprocess
import shutil

pdf_path = r"D:\rso\Documents\Trabalho de IA\Inteligencia-Artificial-Trabalho-Pratico\Descrição do Trabalho final.pdf"
out_txt = os.path.join("projeto", "docs", "descricao_trabalho_final.txt")

os.makedirs(os.path.dirname(out_txt), exist_ok=True)


def try_pypdf():
    try:
        try:
            from pypdf import PdfReader
        except Exception:
            from PyPDF2 import PdfReader
    except Exception:
        return False
    try:
        reader = PdfReader(pdf_path)
        texts = []
        for p in reader.pages:
            t = p.extract_text()
            if t:
                texts.append(t)
        text = "\n\n".join(texts)
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(text)
        print("OK_PDFPY:" + out_txt)
        return True
    except Exception as e:
        print("ERR_PDFPY:", e, file=sys.stderr)
        return False


def try_pdftotext():
    try:
        if shutil.which("pdftotext"):
            res = subprocess.run(["pdftotext", pdf_path, out_txt], check=False)
            if res.returncode == 0:
                print("OK_PDTO:" + out_txt)
                return True
        return False
    except Exception as e:
        print("ERR_PDTO:", e, file=sys.stderr)
        return False


if __name__ == '__main__':
    if try_pypdf():
        sys.exit(0)
    if try_pdftotext():
        sys.exit(0)
    print("FAILED: nenhum método funcionou. Verifique dependências.", file=sys.stderr)
    sys.exit(2)
