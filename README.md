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


controllers/youbot/
Contém o controlador principal do robô e todos os módulos de processamento e decisão.
Essa organização garante compatibilidade total com o sistema de execução do Webots.

youbot.py: controlador principal; integra percepção, navegação e controle.

fuzzy_logic.py: implementação da lógica fuzzy responsável por gerar comandos de movimento.

image_processing.py: processamento de imagens da câmera e interface com a rede neural YOLO.

lidar_processing.py: processamento dos dados do Lidar e cálculo de risco para navegação.

__init__.py: permite importações internas entre os módulos.

models/
Armazena os modelos de redes neurais treinados utilizados pelo sistema.

cnn_model.h5: modelo YOLO/CNN pré-treinado para detecção e classificação dos cubos.

- **worlds/** 
Contém o arquivo de mundo do Webots.

meu_mundo.wbt: arena de simulação com o robô, cubos, caixas e obstáculos.

- **data/**
Contém os dados utilizados no treinamento e validação da rede neural.

- **images/** 
Imagens de treinamento e teste.

- **labels/**
Arquivos de anotação correspondentes.

- **results/**
Armazena resultados gerados durante a execução do sistema.

- **imagens_processadas/**
Imagens com detecções realizadas pela rede neural.

- **logs/**
Arquivos de log para depuração e análise.

- **requirements.txt**
Lista todas as dependências Python necessárias para a execução do projeto

- **README.md**

Arquivo de descrição do projeto, incluindo informações sobre como executar o projeto e como usar o mundo do Webots.