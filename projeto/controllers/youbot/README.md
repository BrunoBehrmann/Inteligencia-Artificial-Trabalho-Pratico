# Relatório Técnico: Modelagem e Controle Reativo para KUKA youBot

Este documento descreve a fundamentação teórica, a arquitetura de software e a modelagem matemática utilizadas no desenvolvimento do controlador autônomo para o robô KUKA youBot no simulador Webots.

---

## 1. Estratégia de Controle: Arquitetura Reativa

Para cumprir o objetivo de navegar sem GPS em um ambiente com obstáculos dinâmicos, adotamos uma **Arquitetura de Controle Reativa**.

### O que isso significa?
Diferente de sistemas que planejam todo o caminho antes de andar (como um GPS de carro), um robô reativo "vive no momento". Ele toma decisões baseadas exclusivamente no que os sensores estão vendo **agora**.

* **Vantagem:** O robô reage instantaneamente a imprevistos.
* **Aplicação no Projeto:** O robô não possui um mapa interno da arena. Ele usa seus sensores para criar um "caminho seguro" em tempo real, desviando de caixotes enquanto busca os cubos.

---

## 2. Estrutura de Arquivos e Módulos

[Image of modular software architecture diagram]

Para garantir um código organizado, escalável e de fácil manutenção, o projeto foi dividido em quatro módulos independentes, seguindo o princípio de separação de responsabilidades:

### A. `youbot.py` (O "Gerente")
Este é o arquivo principal. Ele contém a **Máquina de Estados Finita (FSM)** que orquestra a missão.
* **Função:** Decide *o que* o robô deve fazer no momento (ex: "Procurar Cubo", "Pegar Objeto", "Procurar Caixa").
* **Responsabilidade:** Integra os outros três módulos, chamando-os conforme a necessidade. Ele não faz cálculos complexos, apenas toma decisões de alto nível.

### B. `perception.py` (Os "Olhos")
Este módulo abstrai toda a complexidade dos sensores.
* **Função:** Recebe os dados brutos da câmera e do LiDAR e os transforma em informações úteis.
* **Integração YOLO:** É aqui que a Rede Neural é carregada. O módulo converte a imagem do Webots para o formato OpenCV, executa a detecção e retorna apenas se o alvo (cubo/caixa) foi encontrado e onde ele está.
* **Tratamento do LiDAR:** Filtra os centenas de raios laser para retornar apenas a distância do obstáculo mais próximo no setor frontal.

### C. `fuzzy_control.py` (O "Piloto")
Este módulo contém a inteligência matemática de navegação baseada no artigo de referência.
* **Característica:** É um módulo "cego". Ele não sabe o que é um robô ou uma câmera; ele apenas recebe dois números (`distância` e `erro`) e devolve dois números (`velocidade_esquerda` e `velocidade_direita`).
* **Implementação:** Contém as funções de pertinência triangulares e as 9 regras de inferência Mamdani.

### D. `manipulation.py` (As "Mãos")
Este módulo gerencia a cinemática do braço robótico.
* **Função:** Executa sequências de animação complexas (ex: "Baixar braço -> Abrir garra -> Esperar -> Fechar garra -> Subir braço").
* **Importância:** Remove a poluição visual de contadores de tempo e *delays* do código principal, encapsulando a lógica de manipulação.

---

## 3. Sistema de Percepção (Detalhes Técnicos)

O robô precisa distinguir entre **Alvos** (cubos/caixas) e **Obstáculos** (paredes/outros objetos). Para isso, utilizamos fusão de sensores:

### A. Visão Computacional (RNA - YOLO)
Utilizamos uma Rede Neural (YOLO) para processar a imagem da câmera RGB.
* **Função:** Identificar *o que* é o objeto (Cubo ou Caixa) e *qual* sua cor.
* **Cálculo do Erro:** A RNA nos devolve a posição $X$ do objeto na imagem. Calculamos o **Erro Angular** (o quanto o robô precisa girar) baseando-se na distância do objeto até o centro da imagem.
    * *Erro < 0:* Objeto à esquerda.
    * *Erro > 0:* Objeto à direita.
    * *Erro ≈ 0:* Objeto centralizado (Alvo travado).

### B. LiDAR (Adaptação de Ultrassom)
O trabalho de referência utilizava 3 sensores ultrassônicos (Esquerda, Centro, Direita). Como o YouBot possui um LiDAR (laser):
* **Adaptação:** Dividimos os centenas de raios do LiDAR em setores virtuais.
* **Variável de Entrada:** Utilizamos a menor distância lida no setor central para definir a variável `Distância`, normalizada entre 0 (muito perto/perigo) e 1 (longe/seguro).

---

## 4. Lógica Fuzzy (O "Cérebro" Suavizador)

Para controlar o movimento, não usamos lógica binária ("Se ver obstáculo, pare"). Usamos **Lógica Fuzzy** (Lógica Difusa).

### Por que Fuzzy?
O objetivo matemático principal aqui é **"limitar os sinais de controle"** e **"reduzir erros decorrentes da dinâmica do robô"**.
* O YouBot é alto e pesado. Movimentos bruscos (como uma parada seca) fazem a câmera balançar (perdendo o alvo da RNA) ou as rodas derraparem.
* O Fuzzy cria curvas suaves de aceleração e giro, agindo como um "motorista experiente" que pisa no freio gradualmente.

[Image of fuzzy logic controller block diagram]

### Estrutura Mamdani
O controlador segue o modelo **Mamdani** com:
1.  **Entradas:** Distância do Obstáculo e Erro de Posição do Alvo.
2.  **Saídas:** Velocidade da Roda Esquerda e Velocidade da Roda Direita.
3.  **Regras:** 15 regras que combinam estados como "Perto/Longe" com "Esquerda/Direita".

---

## 5. Modelagem Matemática (A "Física" do Movimento)

O YouBot possui 4 rodas *Mecanum* (omnidirecionais), mas o artigo base utiliza um modelo de **Robô Diferencial** (2 rodas, tipo tanque).

Para aplicar a teoria do artigo no YouBot, realizamos uma adaptação matemática:

### Equações Diferenciais
O movimento do robô é regido pela diferença de velocidade entre o lado esquerdo ($v_l$) e o direito ($v_r$).
* **Rotação ($\dot{\theta}$):** A velocidade angular (giro) é proporcional à diferença entre as velocidades das rodas, dividido pela largura do robô ($2R$), conforme a **Equação 7** do modelo:
    $$\dot{\theta}(t) = -\frac{r}{2R} \omega_r(t) + \frac{r}{2R} \omega_l(t)$$

### Aplicação no Código
Forçamos o YouBot a obedecer a este modelo diferencial agrupando as rodas:
* As saídas do Fuzzy para "Esquerda" são aplicadas nas rodas `Front-Left` e `Rear-Left`.
* As saídas do Fuzzy para "Direita" são aplicadas nas rodas `Front-Right` e `Rear-Right`.

Isso garante que o robô gire sobre seu próprio eixo e faça curvas suaves, validando o uso das equações de dinâmica de motores apresentadas nas referências (Eq. 3 e 4).

---
