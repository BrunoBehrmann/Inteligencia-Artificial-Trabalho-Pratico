# PRD — Projeto YouBot: Coleta e Organização de Cubos (MVP)

## Visão

Entregar um protótipo funcional em Webots onde um YouBot coleta 15 cubos coloridos (verde, azul, vermelho), identifica a cor e deposita cada cubo na caixa correspondente, navegando com segurança pelo ambiente.

## Resumo da alteração

- Substituição da MLP por um detector YOLO para detecção/classificação de cubos.
- Para o LIDAR, adotaremos explicitamente um polar grid agregado por setores (Esquerda / Frente / Direita) como entrada para regras fuzzy.
 - Roadmap reequilibrado para 16 dias, com distribuição das tarefas por complexidade.

## Objetivo principal

Implementar uma solução simples, robusta e reproduzível que cumpra os requisitos do trabalho, priorizando abordagens que acelerem a entrega (uso de modelos pré‑treinados e geração sintética de dados quando possível).

## Critérios de sucesso (aceitação)

- Robô coleta 15 cubos distribuídos aleatoriamente e os deposita nas caixas corretas.
- Navegação evitando obstáculos usando LIDAR (polar grid por setores) com controle fuzzy.
- Detector YOLO classifica cores com precisão prática (meta ≥ 90% em simulação razoável).
- Entrega: vídeo (≤ 15 min) demonstrando execução e repositório com código, modelos e instruções reproduzíveis.

## Escopo do MVP (prioridade alta)

- Simulação em Webots usando o código-base fornecido: `IA_20252/controllers/youbot`.
- **Percepção**:
  - Detector YOLO para localizar e classificar cubos (classes: `green`, `blue`, `red`).
  - Segmentação HSV como fallback/protótipo rápido para depuração e geração de anotações sintéticas.
- **Planejamento e controle**:
  - LIDAR processado como polar grid agregado por setores (Esquerda / Frente / Direita) — entradas para a lógica fuzzy.
  - Regras fuzzy simples que combinam distâncias por setor + ângulo para alvo + estado de carga (tem cubo / não tem) para produzir velocidades e ações.
- **Manipulação**:
  - Uso do controlador de gripper já disponível para abrir/fechar.

## Estados do Robô

Abaixo segue a máquina de estados simplificada que o YouBot seguirá durante a simulação, com as entradas (sensores/variáveis) e saídas (comandos/ações) de cada estado.

Estados (alto nível):

- Idle
  - Descrição: estado inicial/espera antes de iniciar missão.
  - Entradas: comando de start; diagnóstico de sensores (LIDAR/câmera/pronto).
  - Saídas: inicialização de subsistemas; transição para Explore quando `start`.

- Explore / Patrol
  - Descrição: varredura da arena para localizar cubos; comportamento reativo para cobertura.
  - Entradas: leituras LIDAR (setores), detecções parciais da câmera/YOLO, posição atual, mapa local.
  - Saídas: comandos de velocidade (linear, angular), atualização do mapa local, lista de candidatos (bounding boxes) detectados; transição para Approach quando detecta alvo plausível.

- Approach (Ir ao alvo)
  - Descrição: aproximação do cubo selecionado mantendo prevenção de colisões.
  - Entradas: bounding box do alvo (centro, confiança), LIDAR (setores), pose atual, target_angle.
  - Saídas: comandos de navegação fino (velocidade reduzida, correções angulares); transição para Align quando alcance distância de picking.

- Align (Alinhar para pegar)
  - Descrição: alinhamento preciso do gerador de manipulação (braço/gripper) com o cubo.
  - Entradas: visão de próximo alcance (crop), LIDAR frontal, distância ao alvo, estado do braço.
  - Saídas: comandos do braço (trajectória/posição), comandos finos de base (micro‑ajustes); transição para Pick quando pronto.

- Pick (Pegar)
  - Descrição: acionar sequência de preensão e confirmar sucesso.
  - Entradas: posição do gripper, sensores do gripper (se houver), feedback de posição do braço.
  - Saídas: comando `close_gripper`, confirmação `carrying = True`; transição para Transport se pegar com sucesso, caso contrário Retry/Recovery.

- Transport (Transportar para caixa)
  - Descrição: navegar até a caixa correspondente à cor do cubo carregado.
  - Entradas: posição alvo (caixa correspondente), LIDAR, mapa local, estado `carrying`.
  - Saídas: comandos de navegação (trajeto), ajuste fuzzy para evitar obstáculos; transição para AlignDeposit quando próximo da caixa.

- AlignDeposit (Alinhar para depositar)
  - Descrição: posicionamento preciso sobre a área de depósito.
  - Entradas: visão/câmera da área de depósito, LIDAR frontal, posição do braço.
  - Saídas: comandos do braço para posicionamento, abertura do gripper programada; transição para Place.

- Place (Depositar)
  - Descrição: soltar o cubo e confirmar sucesso.
  - Entradas: sensores do gripper, posição do braço, confirmação por visão (se aplicada).
  - Saídas: comando `open_gripper`, `carrying = False`, log do evento (posição, cor, timestamp); transição para Explore (continuar missão) ou Idle se completou 15 cubos.

- Avoidance (Evitar Obstáculos) — estado reativo
  - Descrição: acionado a qualquer momento por leituras críticas do LIDAR (Near em setor frontal) para evitar colisões imediatas.
  - Entradas: LIDAR (setores) com `Near` em Frente/Esquerda/Direita.
  - Saídas: manobra de emergência (parar, virar), atualização de mapa/local path replan; retorna ao estado anterior após resolução.

- Recovery / Error
  - Descrição: tratar falhas (falha de gripper, perda de alvo, stuck) com tentativas de recuperação ou fallback.
  - Entradas: timeouts, falhas de ação (pick fail), sensores inconsistenes.
  - Saídas: tentativas de retry (relocalizar/realinhar), log de erro, transição para Idle ou instrução de intervenção humana se não recuperável.

Notas de integração:

- Cada estado deve expor um pequeno contrato de entradas/saídas (ex.: função `step(inputs) -> (outputs, next_state)`) para facilitar testes e simulação.
- O estado `Avoidance` é prioritário (interrupt) e pode preemptar o fluxo principal até resolução.
- Todos os estados registram eventos no log (state_enter, state_exit, principais decisões) para facilitar avaliação e vídeo de apresentação.

## Requisitos funcionais (essenciais)
1. RF1: Navegar e evitar obstáculos com o LIDAR (polar grid agregado por setores).
2. RF2: Detectar e localizar cubos na cena (bounding box + classe) usando YOLO.
3. RF3: Classificar cor do cubo (verde/azul/vermelho) pelo detector YOLO.
4. RF4: Pegar cubo com a garra e depositar na caixa da cor correta.
5. RF5: Registrar eventos (posição do cubo, cor, confiança, timestamp) em log simples.

## Requisitos não‑funcionais
- Deve rodar em máquina de desenvolvimento comum usando Webots; para treino/fine‑tuning, GPU é recomendada mas não obrigatória (usar Tiny variants para CPU quando necessário).
- Código em Python; dependências mínimas sugeridas: `numpy`, `opencv-python`, `torch` + `ultralytics` (ou `yolov5`), `scikit-fuzzy` opcional. Ferramentas de anotação sugeridas: `labelme` / `roboflow` ou scripts de geração sintética.

## Solução técnica detalhada
### LIDAR — Polar grid por setores

- **Pré‑processamento LIDAR**: converter scan (ângulos/distâncias) em 3 setores agregados — **Esquerda**, **Frente**, **Direita**.
  - Exemplo de partição (3 setores):
    - Esquerda: +60° a +180°
    - Frente: −60° a +60°
    - Direita: −180° a −60°
  - Para cada setor calcular: `min_distance`, `mean_distance`, `angle_of_min`.
  - Normalizar/cap os valores (ex.: 0.2–3.0 m) e mapear para conjuntos fuzzy (Near / Medium / Far).

**Por que setores?**

- Gera variáveis claras e interpretáveis para regras fuzzy (ex.: "se Frente é Near então Pare/Gire").
- Requer menos pré‑processamento que abordagens baseadas em clustering de vetores de obstáculos.

### Variáveis fuzzy (exemplo)

- **Inputs**: `front_dist` (Near/Med/Far), `left_dist`, `right_dist`, `target_angle` (Left/Center/Right), `carrying` (Yes/No).
- **Outputs**: `linear_speed` (Stop/Slow/Fast), `angular_speed` (TurnLeft/TurnRight/Straight), `action` (Move/Pick/Place).

### Regras exemplo (alto‑nível)

- Se `front_dist` é Near e `left_dist` é Far → `angular_speed` = TurnLeft, `linear_speed` = Slow.
- Se `front_dist` é Near e `right_dist` é Far → `angular_speed` = TurnRight, `linear_speed` = Slow.
- Se `front_dist` é Far e `target_angle` é Center → `linear_speed` = Fast, `angular_speed` = Straight.
- Se `carrying` é Yes e `target_angle` é Center e `front_dist` é Far → `action` = Place.
- Se `carrying` é No e `target_angle` é Center e `front_dist` é Near → `action` = Pick.

### YOLO — Dados e treino

- Gerar/anotar dataset com bounding boxes para os cubos (pode usar geração sintética via Webots para acelerar). Aplicar aumentos de iluminação/ruído para robustez.
- Converter anotações para o formato YOLO e fine‑tunar um modelo pré‑treinado (usar Tiny‑YOLO se sem GPU). Salvar o modelo em `projeto/models/`.

## Métricas

- Métrica principal: número de cubos corretamente depositados (meta: 15/15 na simulação).
- Métricas secundárias: precisão por classe / mAP (meta ≥ 90%), colisões por execução (0 desejável), tempo por execução.

## Roadmap detalhado (16 dias distribuídos)

Total: **16 dias úteis** (sugeridos) distribuídos conforme complexidade e dependências:

1. **Setup e integração inicial** — 2 dias
   - Preparar ambiente Webots, integrar leitura LIDAR e câmera no controlador do YouBot; validar streams de sensor.

2. **Protótipo rápido: segmentação HSV + pipeline de debug** — 2 dias
   - Implementar segmentação HSV para depuração e geração rápida de anotações sintéticas; criar scripts para captura de frames do simulador.

3. **Geração / anotação do dataset** — 3 dias
   - Gerar imagens sintéticas com variação de iluminação e posições de cubos; exportar bounding boxes.
   - Refinar anotações e converter para formato YOLO.

4. **Fine‑tuning do YOLO** — 3 dias
   - Fine‑tunar modelo pré‑treinado (preferir Tiny se sem GPU); validar em conjunto com imagens de validação.

5. **Integração YOLO + runtime de inferência** — 2 dias
   - Integrar inferência YOLO ao controlador do YouBot (pipeline: captura → detect → selecionar alvo → navegação).

6. **LIDAR polar grid + controlador fuzzy** — 2 dias
   - Implementar agregação por setores do LIDAR, construção das variáveis fuzzy, conjunto inicial de regras e integração com o sistema de ação.

7. **Testes finais, ajustes e gravação do vídeo** — 1 dia
   - Testes de cenário completo, ajustes de parâmetros, gravação do vídeo de apresentação (≤ 15 min) e organização do repositório.

8. **Fazer Slides** — 1 dia
   - Preparar slides conforme as "Sugestões para Slides": abertura, objetivo, arquitetura, máquina de estados, percepção, LIDAR, resultados e conclusão.

**Observação:** a distribuição assume equipe pequena (1–2 pessoas). Ajuste dias se houver GPU disponível (acelera passo 4) ou mais mão de obra para anotação.

## Riscos e mitigação

- Risco: anotação e fine‑tuning consomem tempo — mitigar com geração sintética e uso de modelos pré‑treinados.
- Risco: inferência lenta em CPU — mitigar escolhendo Tiny variants e reduzindo resolução de entrada.

## Entregáveis (MVP)

- Código que roda em Webots integrando YOLO + LIDAR polar grid + controlador fuzzy.
- Modelo YOLO fine‑tuned em `projeto/models/`.
- Scripts de geração/anotação de dataset e treino.
- Vídeo de apresentação e `README` com instruções de execução.

## Checklist mínimo para entrega

- [ ] Código que roda em Webots com demonstração automática.
- [ ] Modelo YOLO fine‑tuned salvo em `projeto/models/`.
- [ ] Scripts de geração/anotação de dataset e treino.
- [ ] Vídeo de apresentação e `README` com instruções para reproduzir.

---

## Sugestões para Slides

Observação: evitar mostrar trechos de código ou textos longos nos slides — prefira imagens, gráficos, ícones e clipes de vídeo.

### Ordem e conteúdo visual sugeridos

1. **Slide de Abertura**
   - Logo da universidade/turma e título do projeto como arte gráfica; imagem do YouBot como plano de fundo.

2. **Objetivo (visual)**
   - Ícones grandes: coletar, identificar cor, depositar (três ícones em linha).

3. **Arquitetura do Sistema**
   - Diagrama visual com blocos e setas (Câmera → YOLO; LIDAR → Polar Grid → Fuzzy; Controlador → Braço/Gripper).

4. **Máquina de Estados**
   - Diagrama de estados (bolhas/caixas + setas) mostrando transições; cores e ícones por estado.

5. **Percepção — YOLO**
   - Sequência de screenshots com bounding boxes; mosaico: original + overlay do detector + mapa de confiança.

6. **LIDAR — Polar Grid**
   - Visualização do scan agregado por setores (gráfico circular/rose ou barras por setor).

7. **Comportamento / Fuzzy**
   - Infográfico das entradas (setores LIDAR, ângulo, carrying) e saídas (velocidade/ação) com ícones.

8. **Dataset & Treino**
   - Amostras do dataset sintético (imagens com bounding boxes) e gráfico de métrica de validação.

9. **Resultados / Métricas**
   - Gráficos (barras/linhas) com taxa de acerto por cor, número de cubos depositados corretamente.

10. **Demo (vídeo curto)**
   - Clipe de execução da simulação (20–60s) e storyboard com 3‑4 imagens.

11. **Roadmap / Cronograma**
   - Linha do tempo gráfica (16 dias) com blocos coloridos por sprint.

12. **Conclusão / Próximos Passos**
   - Ícones representando melhorias possíveis (ex.: SLAM, deploy real).

13. **Créditos / Contato**
   - Fotos dos integrantes + ícones de contato (YouTube/Email).

### Dicas de design
- Preferir imagens grandes, ícones e legendas curtas; use a fala para explicar detalhes.
- Usar cores consistentes para classes (verde/azul/vermelho) nas figuras e bounding boxes.
- Inserir legendas visuais no vídeo (subtítulos) em vez de texto extenso nos slides.
- Tempo sugerido: 10–12 slides, 12–15 minutos de apresentação, 1–2 minutos de vídeo demonstrativo.
