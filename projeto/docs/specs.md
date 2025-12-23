# Especificação da Técnica de Navegação Autônoma e Coleta de Cubos

## 1. Objetivo do Projeto

O objetivo deste projeto é desenvolver, no simulador **Webots**, um sistema de controle inteligente para um robô móvel terrestre do tipo **YouBot**, capaz de realizar **coleta, transporte e organização autônoma de cubos coloridos** em uma arena delimitada.

Os cubos estão distribuídos aleatoriamente no ambiente e possuem cores distintas (**verde, azul e vermelho**). Para cada cubo encontrado, o robô deverá:

- Detectar visualmente o cubo;
- Identificar sua cor;
- Navegar de forma autônoma e segura até o cubo;
- Coletá-lo utilizando uma garra robótica;
- Transportá-lo até a caixa correspondente à sua cor;
- Depositar o cubo corretamente.

Durante toda a execução da tarefa, o robô deve evitar colisões com paredes, caixas e demais obstáculos presentes no ambiente.

---

## 2. Abordagem Geral da Solução

A solução proposta integra técnicas de **Inteligência Artificial**, **Robótica Móvel** e **Controle Inteligente**, combinando percepção visual, navegação reativa e tomada de decisão contínua.

As técnicas utilizadas são:

- **Rede Neural Convolucional (YOLO)** para detecção e classificação dos cubos;
- **Vector Field Histogram (VFH)** para navegação local e desvio de obstáculos;
- **Lógica Fuzzy** para definição das ações do robô;
- **Máquina de Estados Finitos (FSM)** para coordenação da tarefa de coleta.

Essa abordagem permite navegação orientada a objetivos **sem uso de GPS ou mapas globais**.

---

## 3. Arquitetura Geral do Sistema

A arquitetura do sistema é modular e baseada em fluxo contínuo de dados sensoriais e decisões de controle.

### 3.1 Fluxo de Dados da Arquitetura

- A câmera fornece imagens RGB para a rede neural YOLO;
- O YOLO detecta o cubo, identifica sua cor e estima a direção do alvo;
- O sensor Lidar fornece dados de distância ao módulo VFH;
- O VFH analisa o risco de colisão ao redor do robô;
- A Lógica Fuzzy combina a direção do alvo e o risco de obstáculos;
- O sistema de controle gera comandos de velocidade linear e angular;
- O robô executa o movimento e atualiza o ciclo de percepção.

---

## 4. Percepção Visual com Rede Neural (YOLO)

### 4.1 Função da Rede Neural

A Rede Neural Convolucional **YOLO (You Only Look Once)** é responsável pela percepção visual do ambiente, realizando:

- Detecção dos cubos no campo de visão da câmera;
- Classificação da cor do cubo (verde, azul ou vermelho);
- Estimativa da posição angular do cubo em relação ao eixo frontal do robô.

### 4.2 Dados de Entrada

- Imagens RGB capturadas pela câmera frontal do robô.

### 4.3 Dados de Saída

- Classe do objeto detectado (cor do cubo);
- Bounding box do cubo na imagem;
- Ângulo relativo do cubo em relação ao centro da imagem (`θ_alvo`).

Essas informações são utilizadas para orientar a navegação do robô até o cubo ou até a caixa correspondente.

---

## 5. Navegação Local e Evitação de Obstáculos com VFH

### 5.1 Função do VFH

O **Vector Field Histogram (VFH)** é uma técnica de navegação reativa que utiliza dados do sensor Lidar para representar a ocupação do ambiente em um histograma polar, permitindo a identificação de direções seguras de movimento.

### 5.2 Dados de Entrada

- Leituras do sensor Lidar, representadas como distâncias radiais em múltiplos ângulos.

### 5.3 Processamento

- Conversão das leituras do Lidar em um histograma polar;
- Cálculo do grau de risco associado a cada setor angular;
- Identificação de regiões navegáveis e regiões proibidas.

### 5.4 Dados de Saída

- Grau de risco frontal;
- Grau de risco lateral (esquerda e direita);
- Conjunto de direções seguras para navegação.

---

## 6. Controle das Ações por Lógica Fuzzy

### 6.1 Função da Lógica Fuzzy

A **Lógica Fuzzy** atua como sistema de controle de baixo nível, responsável por transformar informações sensoriais incertas em comandos contínuos de movimento.

Ela realiza a fusão entre:

- A direção do alvo fornecida pela YOLO;
- O grau de risco de colisão fornecido pelo VFH.

### 6.2 Entradas Fuzzy

- Distância ao obstáculo frontal;
- Diferença angular entre o robô e o alvo (`θ_alvo`);
- Grau de risco lateral.

### 6.3 Saídas Fuzzy

- Velocidade linear (`v`);
- Velocidade angular (`ω`).

Essas saídas são aplicadas diretamente aos motores do robô.

---

## 7. Máquina de Estados Finitos para Coleta de Cubos

A execução da tarefa de coleta e organização dos cubos é coordenada por uma **Máquina de Estados Finitos (FSM)** de alto nível.

### 7.1 Estados do Sistema

- **Busca de Cubo**  
  O robô realiza movimentos de varredura até detectar um cubo por meio da YOLO.

- **Aproximação do Cubo**  
  O robô navega em direção ao cubo utilizando YOLO, VFH e Lógica Fuzzy.

- **Alinhamento Fino**  
  Ajuste preciso de posição e orientação para permitir a coleta segura.

- **Coleta do Cubo**  
  A garra robótica é acionada para capturar o cubo.

- **Identificação da Caixa**  
  A cor do cubo determina a caixa de destino.

- **Navegação até a Caixa**  
  O robô navega até a caixa correspondente, evitando obstáculos.

- **Depósito do Cubo**  
  O cubo é liberado dentro da caixa.

- **Retorno à Busca**  
  O robô retorna ao estado inicial até que todos os cubos sejam coletados.

---

## 8. Considerações Finais

A integração entre **YOLO**, **VFH** e **Lógica Fuzzy** permite que o robô execute a tarefa de coleta de cubos de forma autônoma, segura e eficiente, mesmo em ambientes não estruturados. A solução atende integralmente aos requisitos do projeto, explorando conceitos fundamentais de visão computacional, navegação reativa, controle inteligente e robótica móvel.
