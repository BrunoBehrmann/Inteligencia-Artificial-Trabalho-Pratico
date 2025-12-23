# Cronograma Simples — Projeto YouBot (coleta de cubos)

Objetivo: seguir um plano simples e iterativo para implementar percepção, navegação e coleta.

## Visão geral (8 passos)

- **1 — Configurar ambiente**
  - Preparar venv, instalar dependências de `requirements.txt`, configurar Webots.

- **2 — Integração YOLO**
  - Integrar modelo de detecção; testar detecção de cubos e cálculo de `θ_alvo`.

- **3 — Implementar VFH**
  - Implementar algoritmo VFH com dados do Lidar; validar direções seguras.

- **4 — Controlador Fuzzy**
  - Projetar regras fuzzy; gerar velocidades `v` e `ω` a partir de `θ_alvo` e risco.

- **5 — FSM de coleta**
  - Implementar estados: Busca, Aproximação, Alinhamento, Coleta, Navegação até caixa, Depósito, Retorno.

- **6 — Integração da garra**
  - Conectar comandos da garra e rotinas de pegar/deixar; testes no simulador.

- **7 — Testes e validação**
  - Rodar cenários com múltiplos cubos; coletar métricas e ajustar parâmetros.

- **8 — Documentação final**
  - Consolidar resultados, instruções de execução e observações em `projeto/docs`.

## Observações

- Cada item é iterativo: dividir tarefas menores quando necessário.
- Se algum passo demorar mais, ajustar semanas seguintes.
- Para priorização imediata, começar por configurar o ambiente e validar câmera/Lidar.

---

Arquivo gerado automaticamente a partir de `projeto/docs/specs.md`.
