```markdown
# Plano detalhado — Implementação do PRD (YouBot: Coleta e Organização de Cubos)

Este documento contém um plano passo-a-passo em Markdown com tarefas numeradas, subtarefas como checklists e dependências explícitas, baseado no PRD em `projeto/docs/specs.md`.

Notas rápidas:
- Formato: cada item é um checklist `- [ ]` com `ID:` e `Depends:`. IDs em formato `X` ou `X.Y` (onde `X.Y` é subtarefa de `X`).
- Dependências: `Depends: [ids]` indica tarefas que devem ser concluídas antes.

---

## Tarefas Principais e Subtarefas

- [ ] **ID 1:** Setup do ambiente de desenvolvimento
  - Depends: []
  - Contexto: criar ambiente Python reproduzível, instalar dependências básicas e garantir que Webots e controladores estão acessíveis.
  - Subtarefas:
    - [ ] **ID 1.1:** Criar virtualenv em `venv/` e ativar localmente. Depends: []
    - [ ] **ID 1.2:** Atualizar / criar `requirements.txt` com `numpy, opencv-python, torch, ultralytics (ou yolov5), scikit-fuzzy (opcional), pypdf` e instalar. Depends: [1.1]
    - [ ] **ID 1.3:** Verificar versão do Python e path usado pelo VSCode/terminal; ajustar `python` interpreter se necessário. Depends: [1.1]
    - [ ] **ID 1.4:** Confirmar instalação/configuração do Webots (abrir o mundo de teste `projeto/worlds/IA_20252.wbt` e carregar controlador base). Depends: [1.1]

- [ ] **ID 2:** Integração básica de sensores no controlador YouBot
  - Depends: [1]
  - Contexto: garantir leitura contínua de câmera e LIDAR no loop do controlador; expor interfaces simples para consumo por módulos (ex.: `get_camera_frame()`, `get_lidar_scan()`).
  - Subtarefas:
    - [ ] **ID 2.1:** Implementar/validar leitura de frames da câmera no controlador (`controllers/youbot/*`) e salvar amostras em `projeto/data/images/raw/`. Depends: [1]
    - [ ] **ID 2.2:** Implementar/validar leitura de scan LIDAR (ângulos/distâncias) e salvar scans de exemplo em `projeto/data/lidar/`. Depends: [1]
    - [ ] **ID 2.3:** Criar pequenos scripts/testes (`projeto/utils/sensor_tests.py`) que logam formato/shape dos dados e exit code 0. Depends: [2.1,2.2]

- [ ] **ID 3:** Protótipo rápido de percepção (HSV) para debugging e geração de rótulos
  - Depends: [2]
  - Contexto: usar segmentação HSV para detectar cubos por cor; serve para debugging e gerar rótulos sintéticos quando YOLO ainda não estiver pronto.
  - Subtarefas:
    - [ ] **ID 3.1:** Implementar módulo `projeto/utils/hsv_detector.py` que retorna bounding boxes e classes (`green/blue/red`) a partir de uma imagem. Depends: [2.1]
    - [ ] **ID 3.2:** Script `projeto/scripts/capture_and_label.py` que captura frames, roda HSV e grava imagens + `.json` com bounding boxes. Depends: [3.1,2.1]
    - [ ] **ID 3.3:** Validar resultado manualmente em 30 amostras: abrir imagens com overlay. Depends: [3.2]

- [ ] **ID 4:** Implementar agregador Polar Grid do LIDAR
  - Depends: [2]
  - Contexto: converter scan LIDAR em 3 setores (Esquerda/Frente/Direita) com métricas `min_distance, mean_distance, angle_of_min` normalizadas para entrada do fuzzy.
  - Subtarefas:
    - [ ] **ID 4.1:** Escrever função `compute_polar_grid(scan, sector_defs)` em `projeto/utils/lidar_processing.py`. Depends: [2.2]
    - [ ] **ID 4.2:** Implementar normalização/cap (e.g., 0.2–3.0 m) e mapeamento para conjuntos fuzzy (Near/Med/Far). Depends: [4.1]
    - [ ] **ID 4.3:** Unit tests que simulam scans com obstáculos em setores diferentes. Depends: [4.1]

- [ ] **ID 5:** Desenvolver módulo fuzzy core (controlador de baixa complexidade)
  - Depends: [4]
  - Contexto: implementar regras fuzzy simples (entrada: setores+target_angle+carrying → saída: linear/ angular speeds, ação). Preferível usar `scikit-fuzzy` ou implementação leve própria.
  - Subtarefas:
    - [ ] **ID 5.1:** Definir variáveis fuzzy e membership functions (documentar parâmetros). Depends: [4.2]
    - [ ] **ID 5.2:** Implementar inferência fuzzy e defuzzificação em `projeto/control/fuzzy_controller.py`. Depends: [5.1]
    - [ ] **ID 5.3:** Testes unitários para regras principais (ex.: quando frente Near e esquerda Far → turn left). Depends: [5.2]

- [ ] **ID 6:** Máquina de estados do robô (esqueleto) e integração com sensores/controle
  - Depends: [2,5]
  - Contexto: implementar um `State` base e estados concretos (Idle, Explore, Approach, Align, Pick, Transport, AlignDeposit, Place, Avoidance, Recovery) com API `step(inputs)->(outputs,next_state)` para fácil teste.
  - Subtarefas:
    - [ ] **ID 6.1:** Criar `projeto/control/state_machine.py` com base `State` e esqueleto de todos os estados. Depends: [2,5]
    - [ ] **ID 6.2:** Implementar transições e contratos de entrada/saída para cada estado (documentar). Depends: [6.1]
    - [ ] **ID 6.3:** Simular unidade: test harness que injeta leituras LIDAR/YOLO sintéticas para verificar transições. Depends: [6.2]

- [ ] **ID 7:** Geração automática de dataset sintético via Webots
  - Depends: [2,3]
  - Contexto: script que gera variações (posição, rotação, iluminação) e salva imagens + bounding boxes exatas (ground truth) para treinar YOLO.
  - Subtarefas:
    - [ ] **ID 7.1:** Implementar `projeto/scripts/generate_dataset.py` que instancia cenários e grava frames + poses e bounding boxes. Depends: [2.1,2.2]
    - [ ] **ID 7.2:** Criar controles de variação (aleatoriedade seedável: iluminação, número de cubos, posições). Depends: [7.1]
    - [ ] **ID 7.3:** Executar geração mínima: 2000 imagens (ou conforme tempo) e revisar amostras. Depends: [7.2]

- [ ] **ID 8:** Converter anotações para formato YOLO e preparar dataset (train/val/test)
  - Depends: [7]
  - Contexto: converter boxes do formato exportado pelo Webots para o formato YOLO normalizado e organizar pastas conforme `dataset/images` e `dataset/labels`.
  - Subtarefas:
    - [ ] **ID 8.1:** Script `projeto/scripts/convert_to_yolo.py` que gera arquivos `.txt` por imagem. Depends: [7.3]
    - [ ] **ID 8.2:** Dividir dataset em `train/val/test` e gerar `data.yaml`. Depends: [8.1]

- [ ] **ID 9:** Preparar configuração de treino YOLO e ambiente de treino
  - Depends: [8]
  - Contexto: escolher modelo base (Tiny vs full), definir augmentations e criar scripts para treinar reproducivelmente (hyperparameters & logs). Atualizar `requirements.txt` se necessário (`ultralytics` / repo `yolov5`).
  - Subtarefas:
    - [ ] **ID 9.1:** Criar `projeto/train/train_config.yaml` / `data.yaml` com paths e classes. Depends: [8.2]
    - [ ] **ID 9.2:** Implementar script `projeto/train/run_train.sh` (ou `run_train.py`) que roda treino com checkpoints salvos em `projeto/models/`. Depends: [9.1]

- [ ] **ID 10:** Fine‑tuning do modelo YOLO
  - Depends: [9]
  - Contexto: treinar modelo com validação, monitorar métricas, salvar melhor checkpoint; usar Tiny se sem GPU para tempo reduzido.
  - Subtarefas:
    - [ ] **ID 10.1:** Rodar treino inicial com subset rápido (smoke run) e confirmar pipeline. Depends: [9.2]
    - [ ] **ID 10.2:** Rodar treino completo, registrar métricas (loss, mAP) e salvar `best.pt` em `projeto/models/`. Depends: [10.1]

- [ ] **ID 11:** Exportar e validar modelo para inferência (PT/ONNX)
  - Depends: [10]
  - Contexto: exportar checkpoint para formato de inferência, criar script de inferência `projeto/utils/infer.py` e medir precisão/latência em amostras. Documentar versão do modelo.
  - Subtarefas:
    - [ ] **ID 11.1:** Exportar `best.pt` para `best.onnx`/TorchScript se necessário. Depends: [10.2]
    - [ ] **ID 11.2:** Validar inferência com `projeto/utils/infer.py` em 100 imagens e gerar relatório simples (precisão por classe). Depends: [11.1]

- [ ] **ID 12:** Integrar inferência YOLO no controlador em runtime
  - Depends: [11,2]
  - Contexto: adicionar pipeline de captura → preprocess → detect → postprocess no loop do controlador com foco em latência (usar batch=1, threads ou async se necessário).
  - Subtarefas:
    - [ ] **ID 12.1:** Implementar wrapper `projeto/control/yolo_runtime.py` que carrega modelo e expõe `detect(frame)`. Depends: [11.2]
    - [ ] **ID 12.2:** Integrar chamadas de `detect()` no loop do controlador, priorizando frequência e latência aceitável. Depends: [12.1,2.1]
    - [ ] **ID 12.3:** Testar end-to-end detecção em simulação e medir FPS/latência. Depends: [12.2]

- [ ] **ID 13:** Implementar sequência de pick/place no braço usando controladores existentes
  - Depends: [6]
  - Contexto: usar `projeto/controllers/youbot/arm.py` e `gripper.py` para compor funções de alto nível `approach_and_pick(target)` e `transport_and_place(box_pos)` com tratamento de falhas.
  - Subtarefas:
    - [ ] **ID 13.1:** Criar `projeto/control/manipulation.py` com funções `open_gripper()`, `close_gripper()`, `move_arm_to(pose)`. Depends: [6]
    - [ ] **ID 13.2:** Implementar retries e condições de timeout; log de eventos de pick/place. Depends: [13.1]
    - [ ] **ID 13.3:** Testes em simulação para pick de 1 cubo. Depends: [13.2,12]

- [ ] **ID 14:** Integração completa: percepção + planejamento + manipulação
  - Depends: [12,5,13,6]
  - Contexto: conectar saída do detector (bounding box + class) ao fluxo de seleção de alvo, gerar `target_angle`, usar fuzzy para navegação e sequência de manipulação para completar ciclo de coleta/deposição.
  - Subtarefas:
    - [ ] **ID 14.1:** Implementar alvo selecionador `projeto/control/target_selector.py` (prioriza confiança + proximidade). Depends: [12]
    - [ ] **ID 14.2:** Integrar selector → state machine → fuzzy → manipulation e verificar ciclo completo para 1 cubo. Depends: [14.1,13,6,5]
    - [ ] **ID 14.3:** Expandir testes para múltiplos cubos (até 15) em cenário controlado. Depends: [14.2]

- [ ] **ID 15:** Logging, métricas e visualização de resultados
  - Depends: [14]
  - Contexto: registrar eventos (posição, cor, confiança, timestamp), colisões, sucesso de pick/place e gerar scripts para visualizar métricas (JSON → gráficos).
  - Subtarefas:
    - [ ] **ID 15.1:** Implementar logger central `projeto/utils/logger.py` que grava JSON/CSV por execução. Depends: [14]
    - [ ] **ID 15.2:** Criar script `projeto/scripts/plot_metrics.py` para gerar gráficos de desempenho (mAP, cubos coletados, colisões). Depends: [15.1]

- [ ] **ID 16:** Testes end‑to‑end e ajuste de robustez
  - Depends: [15]
  - Contexto: executar múltiplas runs aleatórias para estimar métricas reais; ajustar thresholds do detector, regras fuzzy e parâmetros do state machine.
  - Subtarefas:
    - [ ] **ID 16.1:** Executar N=30 runs com seed variável e coletar métricas. Depends: [15.1]
    - [ ] **ID 16.2:** Ajustar parâmetros críticos e documentar alterações (registros de versão). Depends: [16.1]

- [ ] **ID 17:** Gravação do vídeo de demonstração e seleção de trechos
  - Depends: [16]
  - Contexto: preparar execução para gravação, capturar cenas chave e montar um vídeo ≤15 min para apresentação.
  - Subtarefas:
    - [ ] **ID 17.1:** Criar script `projeto/scripts/record_demo.py` que executa cenário e grava vídeo. Depends: [16]
    - [ ] **ID 17.2:** Selecionar clipes e montar vídeo final (ferramenta sugerida: ffmpeg). Depends: [17.1]

- [ ] **ID 18:** Documentação final e README de reprodução
  - Depends: [1,9,11,12,14,15,17]
  - Contexto: instruções claras para replicar ambiente, treinar modelo, rodar simulação e reproduzir demo.
  - Subtarefas:
    - [ ] **ID 18.1:** Escrever `README.md` com passos rápidos (setup, treino, run). Depends: [1,9,11,12]
    - [ ] **ID 18.2:** Incluir seção `HOWTO: Record demo` e link para vídeo. Depends: [17]

- [ ] **ID 19:** Preparar slides de apresentação (1 dia)
  - Depends: [15,17,18]
  - Contexto: gerar slides seguindo as sugestões do PRD; exportar `.pptx` ou `.pdf` em `projeto/docs/slides/`.
  - Subtarefas:
    - [ ] **ID 19.1:** Criar esqueleto dos slides com títulos e imagens (arquitetura, estados, métricas). Depends: [15]
    - [ ] **ID 19.2:** Inserir resultados e clipes selecionados do vídeo. Depends: [17,15]

- [ ] **ID 20:** Otimização e fallback para CPU (Tiny/quantização) + CI básica
  - Depends: [11,12]
  - Contexto: garantir que haja alternativa para rodar em CPU e adicionar scripts de verificação/linting no repositório.
  - Subtarefas:
    - [ ] **ID 20.1:** Converter modelo para Tiny/ONNX e avaliar latência em CPU; documentar tradeoffs. Depends: [11]
    - [ ] **ID 20.2:** Adicionar scripts de verificação (`make test-smoke`, lint) e um job simples de CI (ex.: GitHub Actions). Depends: [1,12]

---

## Observações sobre dependências e ordem

- Todas as tarefas listadas possuem dependências explícitas; não há tarefas órfãs — cada caminho leva desde `ID 1` (setup) até `ID 19` (slides) e `ID 17` (vídeo).  
- Se houver limitação de GPU, priorizar `ID 9` com Tiny variant e reduzir tamanho de dataset para um smoke-run antes do treino completo.  
- Prioridade sugerida para execução: 1 → 2 → (3,4) → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20.


## Sprints sugeridos (3–5 dias)

Observação: sprints abaixo são sugestões iniciais; ajuste cargas/datas conforme disponibilidade da equipe. Todas as tarefas listadas no plano anterior foram mapeadas para um sprint (não há tarefas órfãs).

- **Sprint 1 — 2025-12-18 to 2025-12-21 (4 dias)**
  - Objetivo: preparação do ambiente, integração de sensores e protótipo HSV para gerar rótulos rápidos.
  - Tarefas atribuídas:
    - ID 1 (Setup do ambiente de desenvolvimento)
    - ID 2 (Integração básica de sensores no controlador YouBot)
    - ID 3 (Protótipo rápido de percepção (HSV))

- **Sprint 2 — 2025-12-22 to 2025-12-25 (4 dias)**
  - Objetivo: adicionar pré‑processamento LIDAR, definir o controlador fuzzy e criar o esqueleto da máquina de estados.
  - Tarefas atribuídas:
    - ID 4 (Implementar agregador Polar Grid do LIDAR)
    - ID 5 (Desenvolver módulo fuzzy core)
    - ID 6 (Máquina de estados do robô (esqueleto))

- **Sprint 3 — 2025-12-26 to 2025-12-29 (4 dias)**
  - Objetivo: gerar dataset sintético, converter para YOLO e preparar configuração de treino.
  - Tarefas atribuídas:
    - ID 7 (Geração automática de dataset sintético via Webots)
    - ID 8 (Converter anotações para formato YOLO)
    - ID 9 (Preparar configuração de treino YOLO)

- **Sprint 4 — 2025-12-30 to 2026-01-02 (4 dias)**
  - Objetivo: treino inicial/fine‑tuning, exportar modelo, integrar runtime e implementar manipulação básica; iniciar integração completa.
  - Tarefas atribuídas:
    - ID 10 (Fine‑tuning do modelo YOLO)
    - ID 11 (Exportar e validar modelo para inferência)
    - ID 12 (Integrar inferência YOLO no controlador em runtime)
    - ID 13 (Implementar sequência de pick/place no braço)

- **Sprint 5 — 2026-01-03 to 2026-01-06 (4 dias)**
  - Objetivo: integração final, logging, testes E2E, vídeo e documentação; otimizações/CI.
  - Tarefas atribuídas:
    - ID 14 (Integração completa: percepção + planejamento + manipulação)
    - ID 15 (Logging, métricas e visualização de resultados)
    - ID 16 (Testes end‑to‑end e ajuste de robustez)
    - ID 17 (Gravação do vídeo de demonstração e seleção de trechos)
    - ID 18 (Documentação final e README de reprodução)
    - ID 19 (Preparar slides de apresentação)
    - ID 20 (Otimização e fallback para CPU + CI básica)