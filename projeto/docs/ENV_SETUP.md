**Setup do ambiente (virtualenv)**

- Local do script: projeto/scripts/setup_env.ps1 (Windows PowerShell)
- Alternativa POSIX: projeto/scripts/setup_env.sh

Passos rápidos (PowerShell):

1. Abra PowerShell em modo usuário (não admin) no diretório do repositório.
2. Execute:

```powershell
# cria venv e instala dependências (CPU torch por padrão)
.\n+projeto\scripts\setup_env.ps1
```

Para instalar com suporte GPU, siga as instruções em https://pytorch.org e, opcionalmente, passe `-Gpu` ao script (o script apenas avisa; instale a wheel apropriada manualmente antes/ depois).

Exemplo (bash / WSL / macOS / Linux):

```bash
bash projeto/scripts/setup_env.sh
# ou para GPU (nota: script não instala automaticamente wheels CUDA)
bash projeto/scripts/setup_env.sh --gpu
```

Ativação do ambiente:

- PowerShell: `& venv\Scripts\Activate.ps1`
- cmd.exe: `venv\Scripts\activate.bat`
- bash: `source venv/bin/activate`

Observações:
- `requirements.txt` no root contém as dependências recomendadas. Ajuste conforme sua GPU/versões.
- Se a instalação de `torch` falhar, visite https://pytorch.org para comandos específicos do seu CUDA/OS.