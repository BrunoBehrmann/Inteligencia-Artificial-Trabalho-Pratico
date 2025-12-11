# MATA64 – Inteligência Artificial – Trabalho Prático

**Universidade Federal da Bahia (UFBA)**  
**Instituto de Computação (IC)**  
**Departamento de Ciência da Computação (DCC)**  
**Semestre:** 2025.2  
**Docente:** Luciano Oliveira  
**Discente:** *Bruno de Sousa Behrmann / Reginaldo Silva de Oliveira*  

## Objetivo

O projeto consiste no desenvolvimento de um sistema de **aprendizagem de máquina aplicado à robótica**, utilizando o simulador **Webots**. O robô utilizado será o **YouBot**, que deverá realizar autonomamente uma tarefa de coleta, classificação e organização de objetos em uma arena.  
A documentação e os arquivos de suporte encontram-se no diretório *IA_20252* fornecido junto ao projeto.

## Visão Geral do Sistema

O robô deve navegar pelo ambiente, localizar 15 cubos coloridos (verde, azul ou vermelho), coletá-los com a garra e depositá-los nas caixas correspondentes. Durante toda a operação, o robô deve evitar obstáculos, utilizando apenas informações sensoriais — o uso de GPS é estritamente proibido.

### Sensores e Ambiente

- **LIDAR:** Utilizado para detecção de obstáculos e mapeamento do ambiente.  
- **Câmera RGB:** Responsável pela identificação das cores dos cubos.  
- **Sensores adicionais:** Permitidos, desde que justificados.  
- **Arena:** Contém obstáculos fixos e cubos distribuídos aleatoriamente (rotina de spawn não pode ser alterada).

### Funcionalidades Principais

- **Navegação Autônoma:** Baseada exclusivamente em LIDAR e câmera.  
- **Detecção de Obstáculos:** Deve empregar ao menos uma RNA (MLP ou CNN).  
- **Classificação de Cubos:** Visão computacional para identificação das três cores.  
- **Coleta de Objetos:** Controle do braço e da garra do YouBot.  
- **Depósito:** Colocação dos cubos nas caixas correspondentes.  
- **Controle Fuzzy:** Sistema de lógica fuzzy para tomada de decisões e ajustes finos de movimento.

## Exigências de Projeto

1. **Uso obrigatório de técnicas de IA:**  
   - Uma ou mais Redes Neurais Artificiais.  
   - Sistema de Lógica Fuzzy para controle do robô.  
2. **Navegação sem GPS:** Toda a movimentação deve depender dos sensores disponíveis.  
3. **Código-base:** Pode ser utilizado, modificado ou substituído (Python ou C).  
4. **Uso de bibliotecas e modelos externos:** Permitido, desde que claramente explicado no vídeo da apresentação.

## Componentes e Código-base

Os módulos de controle do YouBot em Python encontram-se em: IA_20252/controllers/youbot
A alternativa em C está localizada em: IA_20252/libraries/youbot_control/src.
Todo o ambiente simulado está incluído no pacote *IA_20252* fornecido com o projeto.

## Estrutura de pastas e arquivos


- **worlds/** 

 Contém o arquivo de mundo do Webots, que é usado para simular o ambiente do robô. O arquivo meu_mundo.wbt é o mundo que você criou no Webots.

 - **controllers/**

 Contém o meu_controller.py, código do controlador do robô. O controlador é responsável por ler os dados dos sensores, processar as informações e enviar comandos para os atuadores do robô.

- **models/**

Contém os modelos de rede neural e lógica fuzzy que você usará no projeto.
    - cnn_model.h5: Modelo de rede neural CNN pré-treinado para detecção de objetos.
    - fuzzy_logic.py: Implementação da lógica fuzzy para a garra do robô, responsável por controlar a força de agarrar e soltar objetos.

- **utils/**

Contém funções utilitárias para processamento de imagens e dados do Lidar.
    - image_processing.py: Funções para processar as imagens da câmera, incluindo conversão de formatos, filtragem e detecção de bordas.
    - lidar_processing.py: Funções para processar os dados do Lidar, incluindo filtragem e detecção de obstáculos.

- **data/**

Contém os dados de treinamento e teste para a rede neural.
    - images/: Imagens de treinamento e teste para a rede neural.
    - labels/: Etiquetas correspondentes às imagens, indicando a posição e a classe dos objetos.

- **results/**

Contém os resultados do processamento e logs do projeto.
    - imagens_processadas/: Imagens processadas pela rede neural, incluindo as detecções de objetos.
    - logs/: Logs do projeto, incluindo informações de erro e debug.

- **worlds/**

Contém o arquivo de mundo do Webots, que é usado para simular o ambiente do robô.
    - meu_mundo.wbt: O mundo que você criou no Webots, incluindo o robô, os objetos e o ambiente.

- **requirements.txt**

Lista de dependências do projeto, incluindo as bibliotecas e pacotes necessários para executar o código.


- **README.md**

Arquivo de descrição do projeto, incluindo informações sobre como executar o projeto e como usar o mundo do Webots.