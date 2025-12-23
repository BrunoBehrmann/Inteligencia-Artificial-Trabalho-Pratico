# Polar Grid com Ações Discretas

## Ideia central

O **Polar Grid** é um método de navegação local onde o espaço ao redor
do robô é dividido em **setores angulares**. Cada setor recebe um valor
de risco baseado na proximidade de obstáculos detectados pelo Lidar.

Neste modelo, o Polar Grid **não gera um ângulo contínuo de movimento**.
Ele apenas avalia o risco das direções.\
A decisão final é feita escolhendo **uma ação discreta**.

------------------------------------------------------------------------

## Ações permitidas

O robô só pode executar uma das seguintes ações:

-   **FRENTE** -- deslocamento retilíneo para frente\
-   **TRÁS** -- deslocamento retilíneo para trás\
-   **GIRAR_ESQUERDA** -- rotação no próprio eixo (sentido
    anti-horário)\
-   **GIRAR_DIREITA** -- rotação no próprio eixo (sentido horário)

------------------------------------------------------------------------

## Arquitetura em camadas

### 1. Percepção

-   Leitura do Lidar
-   Conversão das leituras em um **histograma polar**
-   Cada setor angular representa o risco de colisão naquela direção

### 2. Avaliação

Cada ação está associada a um **conjunto fixo de setores**:

-   Frente → setores próximos de 0°
-   Trás → setores próximos de ±180°
-   Giro esquerda → setores laterais esquerdos
-   Giro direita → setores laterais direitos

O risco da ação é calculado a partir desses setores (mínimo ou máximo
das distâncias).

### 3. Decisão

-   Calcula-se o risco de cada ação
-   Escolhe-se a ação **mais segura**
-   Pode-se impor prioridade para frente ou penalizar ré

### 4. Controle

-   A ação escolhida é convertida em velocidades fixas dos motores
-   Não há curvas contínuas
-   O robô apenas anda reto ou gira no próprio eixo

------------------------------------------------------------------------

## Vantagens

-   Simples de implementar
-   Comportamento previsível
-   Fácil depuração
-   Compatível com robôs diferenciais simples

## Limitações

-   Movimento menos suave
-   Pode gerar ciclos de gira-e-andar
-   Menor eficiência de caminho

------------------------------------------------------------------------

## Observação importante

Mesmo com ações discretas, o método **continua sendo um Polar Grid**,
pois a avaliação do espaço é angular e baseada em histograma.

O que muda é apenas a **política de controle**.
