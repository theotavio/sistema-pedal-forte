# Pedal Forte Bicicletas - Sistema de Planejamento dos Recursos de Manufatura (MRP II)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8%2B-11557C?style=for-the-badge&logo=python&logoColor=white)

---

## Visão Geral do Sistema

O **Sistema Pedal Forte Bicicletas** é uma solução completa e moderna de **Planejamento dos Recursos de Manufatura (MRP II - *Manufacturing Resource Planning*)**, concebida especificamente para as particularidades produtivas de uma fábrica de bicicletas.

O sistema integra planejamento estratégico, tático e operacional:
1. **Engenharia de Produto (BOM Multinível):** Cadastro hierárquico em até 3 níveis (PA -> SA -> MP) com algoritmo recursivo de explosão e prevenção contra ciclos.
2. **Controle de Estoque & Auditoria (Kardex Perpétuo):** Movimentações rastreáveis com saldo não-negativo e histórico imutável.
3. **Plano Mestre de Produção (MPS):** Projeção de demanda semanal para produtos acabados no horizonte de 8 semanas.
4. **Motor de Cálculo MRP:** Motor algorítmico próprio em Python puro (sem frameworks ERP de terceiros) que calcula necessidades brutas, estoque projetado, necessidades líquidas, recebimentos planejados e liberações planejadas.
5. **Planejamento de Capacidade (CRP):** Cálculo de carga semanal em horas por centro de trabalho com destaque imediato de sobrecarga.
6. **Controle de Chão de Fábrica:** Fluxo de ordens de produção (OP) e compra (OC) com apontamento atômico de produção e baixa automática na BOM.
7. **Custeio Padrão por Absorção:** Algoritmo recursivo que percorre a estrutura de produto computando custo de matérias-primas e mão de obra dos centros de trabalho.
8. **Gráficos Gerenciais & Exportação:** Visualização interativa em tela e geração de arquivos PNG via Matplotlib, além de exportação de inventário e ordens em formato CSV compatível com Excel e LibreOffice.

---

## Requisitos Funcionais (RF)

| Requisito | Descrição | Módulo Responsável |
| :--- | :--- | :--- |
| **RF01** | Exibir um menu principal com as opções do sistema. | `frontend/main_window.py` |
| **RF02** | Cadastrar, listar e alterar itens (código, descrição, tipo PA/SA/MP, unidade, custo unitário, lead time, estoque de segurança e lote mínimo). | `backend/services/item_service.py` |
| **RF03** | Cadastrar a estrutura de produto (BOM) em até 3 níveis (PA -> SA -> MP), informando componentes por pai e quantidade por unidade, exibindo-a indentada (explosão) com o nível de cada componente. | `backend/services/bom_service.py` |
| **RF04** | Registrar movimentações de estoque (entrada, saída e ajuste) com data, quantidade e documento/motivo, atualizando o saldo do item. | `backend/services/inventory_service.py` |
| **RF05** | Consultar o saldo e o kardex de um item, alertando quando o saldo estiver abaixo do estoque de segurança. | `backend/services/inventory_service.py` |
| **RF06** | Cadastrar centros de trabalho (capacidade em horas/semana e custo-hora) e informar, para cada item fabricado, o centro que o produz e o tempo por unidade (roteiro de operação única). | `backend/services/work_center_service.py` |
| **RF07** | Cadastrar e alterar o Plano Mestre de Produção (MPS): demanda dos produtos acabados por semana, em um horizonte de 8 semanas. | `backend/services/mps_service.py` |
| **RF08** | Executar o cálculo MRP para todos os itens e exibir o registro de um item escolhido por semana: necessidade bruta, recebimentos programados, estoque projetado, necessidade líquida, recebimentos planejados e liberações planejadas. | `backend/services/mrp_service.py` |
| **RF09** | Gerar ordens planejadas a partir do MRP: ordens de produção (OP) para itens fabricados e ordens de compra (OC) para matérias-primas, com semana de liberação e de entrega. | `backend/services/mrp_service.py` |
| **RF10** | Permitir firmar, liberar e encerrar ordens, controlando o status de cada uma (`PLANEJADA` -> `FIRME` -> `LIBERADA` -> `ENCERRADA`). | `backend/services/order_service.py` |
| **RF11** | Apontar a produção de uma OP liberada pela quantidade total: baixar os componentes do estoque, dar entrada no item produzido e encerrar a OP, rejeitando o apontamento se faltar componente. | `backend/services/order_service.py` |
| **RF12** | Exibir a carga x capacidade (CRP) de cada centro de trabalho por semana, sinalizando as semanas com sobrecarga. | `backend/services/crp_service.py` |
| **RF13** | Calcular o custo padrão dos itens fabricados (materiais + mão de obra), percorrendo a estrutura de produto de forma recursiva. | `backend/services/cost_service.py` |
| **RF14** | Exportar em CSV a posição de estoque e a lista de ordens (armazenadas na pasta `data/csv/`). | `backend/services/export_service.py` |
| **RF15** | Persistir todos os dados em SQLite. | `backend/database.py` |
| **RF16** | Gerar, com a biblioteca matplotlib, gráficos de gestão e acompanhamento, exibidos na tela e salvos em PNG na pasta `data/graficos/`: | `backend/services/chart_service.py` |
| **RF16.1** | Posição de estoque: saldo atual x estoque de segurança de cada item (barras). | `backend/services/chart_service.py` |
| **RF16.2** | Estoque projetado de um item nas 8 semanas do MRP, com linha do estoque de segurança. | `backend/services/chart_service.py` |
| **RF16.3** | Ordens de produção e de compra por semana de entrega (chegada), diferenciando OP e OC (barras empilhadas). | `backend/services/chart_service.py` |
| **RF16.4** | Carga x capacidade de um centro de trabalho por semana, destacando as semanas com sobrecarga. | `backend/services/chart_service.py` |

---

## Regras de Negócio (RN)

* **RN01:** O código do item é único e segue o formato `Tipo-Número` (ex: `PA-001`, `SA-020`, `MP-201`). Itens PA e SA são fabricados; itens MP são comprados e não possuem estrutura.
* **RN02:** O saldo de estoque nunca pode ficar negativo: uma saída ou consumo maior que o saldo deve ser rejeitado com mensagem explicativa.
* **RN03:** A estrutura tem no máximo 3 níveis: um PA pode ter como componentes SA e MP; um SA, apenas MP; MP não possui estrutura. O cadastro rejeita componentes que violem essa regra, o que também impede ciclos na BOM.
* **RN04:** O MRP processa os itens por tipo: primeiro as PA, depois as SA e por fim as MP, de modo que a necessidade bruta de um componente seja a soma das liberações planejadas de todos os seus pais multiplicadas pela quantidade por unidade.
* **RN05:** Necessidade líquida na semana $t$:
  $$NL(t) = \max(0, NB(t) + ES - (EP(t - 1) + RP(t)))$$
  em que $NB$ é a necessidade bruta, $ES$ o estoque de segurança, $EP$ o estoque projetado e $RP$ os recebimentos programados.
* **RN06:** Quando houver necessidade líquida ($NL(t) > 0$), o recebimento planejado é o maior valor entre a necessidade líquida e o lote mínimo do item:
  $$RecP(t) = \max(NL(t), \text{lote\_minimo})$$
* **RN07:** A liberação planejada ocorre na semana do recebimento menos o lead time ($t_{lib} = t - LT$). Se cair antes da semana 1 ($t_{lib} < 1$), a ordem é marcada como `ATRASADA` e gera uma mensagem de exceção.
* **RN08:** Apenas ordens `FIRME` ou `LIBERADA` entram como recebimentos programados ($RP$); ordens `PLANEJADA` e `ATRASADA` não firmadas são apagadas e recalculadas a cada execução do MRP.
* **RN09:** Carga do centro na semana = soma de $(\text{quantidade da OP} \times \text{tempo unitário do roteiro})$ das OPs liberadas naquela semana; há sobrecarga quando a carga supera a capacidade nominal.
* **RN10:** Toda movimentação de estoque deve ser registrada no histórico (kardex) com data e documento de origem e não pode ser excluída; correções são feitas por ajuste.

---

## Requisitos Não Funcionais (RNF)

* **RNF01:** Código 100% aderente ao padrão de estilo **PEP8** (validado com `flake8` com 0 violações).
* **RNF02:** Sistema organizado em pacotes e módulos coesos e desacoplados.
* **RNF03:** Tratamento abrangente de erros e validação de entradas em todos os pontos de interação com o usuário.
* **RNF04:** Execução validada em ambiente **Linux**.
* **RNF05:** Persistência relacional em banco de dados **SQLite3** com chaves estrangeiras ativas.
* **RNF06:** Lógica de negócio (MRP, CRP, custos e estoques) implementada em **Python puro sem bibliotecas prontas de ERP/MRP**.
* **RNF07:** Interface gráfica com **PySide6 (Qt6)** com **modo claro por padrão**, design moderno, limpo, componentes refinados e **animações modernas presentes** (`QPropertyAnimation`).

---

## Decisões de Projeto

1. **Separação em Camadas Limpas (Backend / Frontend):**
   * A camada `backend/` não possui qualquer dependência gráfica e pode ser executada em modo script, CLI ou API.
   * A camada `frontend/` consome os serviços por injeção direta de dependência, tratando exceções de domínio (`ErroRegraNegocio`) e exibindo diálogos explicativos.
2. **Motor Algorítmico Próprio do MRP (Pure Python):**
   * Para atender ao RNF06, os cálculos de explosão de necessidades brutas, cálculo de estoque projetado com saldo acumulado e loteamento mínimo foram construídos utilizando listas, matrizes e dicionários nativos.
3. **Recursividade no Custeio e Explosão:**
   * As funções `explodir_arvore_estrutura` e `calcular_custo_padrao_item` utilizam recursividade para percorrer até o nível mais profundo da árvore de componentes, somando custos de compra para matérias-primas e acumulando tempo de centro de trabalho para mão de obra.
4. **Persistência Segura com SQLite:**
   * Uso de transações atômicas no apontamento de produção (RF11): o débito de todos os insumos e o crédito do produto acabado ocorrem em um único bloco transacional, garantindo que nunca ocorra baixa parcial se faltar algum item.
5. **Design Visual e Ergonomia (RNF07):**
   * Aplicação de folha de estilos QSS (`frontend/styles.py`) inspirada nas diretrizes de design modernas (Tailwind UI e Linear), com barra lateral executiva em tom azul-ardósia escuro (`#0F172A`), canvas suave neutro (`#F1F5F9`) para evitar ofuscamento ("branco estourado"), cartões brancos com bordas definidas (`#CBD5E1`), cabeçalhos de tabela contrastantes (`#E2E8F0`), paletas semânticas temáticas nos indicadores de desempenho (KPIs) e alternância fluida entre as 12 visões do sistema.
6. **Otimização de Desempenho e Cache Inteligente:**
   * Aplicação de arquitetura reativa com carregamento sob demanda (*lazy-loading*), invalidação orientada a eventos (`Signal` do Qt) e cache de dados entre as 12 visões, reduzindo o tempo médio de transição de abas para ~0,068 ms e desacoplando a renderização gráfica do Matplotlib da gravação em disco.

---

## Estrutura de Pastas do Projeto

```text
sistema-pedal-forte/
├── backend/
│   ├── __init__.py
│   ├── database.py              # Conexão SQLite e criação das tabelas
│   ├── exceptions.py            # Hierarquia de exceções especializadas
│   ├── models.py                # Dataclasses de domínio do MRP II
│   ├── seed_data.py             # Carga inicial com dados da fábrica de bicicletas
│   └── services/
│       ├── __init__.py
│       ├── item_service.py       # CRUD e regras de itens (RF02 / RN01)
│       ├── bom_service.py        # Estrutura de produto e explosão multinível (RF03 / RN03)
│       ├── inventory_service.py  # Estoque, Kardex e validação não-negativa (RF04 / RF05 / RN02 / RN10)
│       ├── work_center_service.py# Centros produtivos e roteiros (RF06)
│       ├── mps_service.py        # Plano Mestre de Produção em 8 semanas (RF07)
│       ├── mrp_service.py        # Algoritmo de cálculo do MRP (RF08 / RF09 / RN04-RN08)
│       ├── order_service.py      # Ciclo de ordens e apontamento de chão de fábrica (RF10 / RF11)
│       ├── crp_service.py        # Cálculo de Carga x Capacidade (RF12 / RN09)
│       ├── cost_service.py       # Custo padrão recursivo materiais + MO (RF13)
│       ├── export_service.py     # Exportação em CSV de estoques e ordens (RF14)
│       └── chart_service.py      # Geração de gráficos Matplotlib e PNG (RF16)
├── frontend/
│   ├── __init__.py
│   ├── styles.py                # Estilos visuais modernos em modo claro (QSS)
│   ├── animations.py            # Efeitos e transições animadas (QPropertyAnimation)
│   ├── main_window.py           # Janela principal com sidebar e stacked widget (RF01)
│   └── views/
│       ├── __init__.py
│       ├── dashboard_view.py     # Painel geral com KPIs e alertas críticos
│       ├── items_view.py         # Gestão de itens cadastrados
│       ├── bom_view.py           # Árvore multinível da BOM e inclusão guiada
│       ├── inventory_view.py     # Posição física e histórico do Kardex
│       ├── work_centers_view.py  # Centros de trabalho e associação de roteiros
│       ├── mps_view.py           # Matriz editável do Plano Mestre (8 semanas)
│       ├── mrp_view.py           # Matriz detalhada do MRP e painel de exceções
│       ├── orders_view.py        # Gerenciamento de OP/OC e apontamento (RF11)
│       ├── crp_view.py           # Relatório semanal de carga x capacidade
│       ├── costs_view.py         # Detalhamento de custo padrão por absorção
│       ├── charts_view.py        # Telas interativas dos gráficos Matplotlib
│       └── export_view.py        # Central de exportação de dados em CSV
├── data/
│   ├── pedal_forte.db           # Banco de dados SQLite
│   ├── csv/                     # Diretório de exportação de relatórios em CSV (RF14)
│   └── graficos/                # Pasta de armazenamento dos gráficos gerados em PNG (RF16)
├── videos/                      # Diretório de vídeos de demonstração (disponíveis via GitHub Releases)
├── main.py                      # Ponto de entrada do sistema
├── .gitignore                   # Arquivos e diretórios ignorados pelo Git
└── README.md                    # Documentação técnica e guia do usuário
```

---

## Vídeos de Demonstração (GitHub Releases)

Os vídeos completos de apresentação do sistema e auditoria do código fonte superam o limite de 100 MB por arquivo para armazenamento direto no Git:
* [**`demonstracao_codigo.mp4`**](https://github.com/theotavio/sistema-pedal-forte/releases/download/v1.0.0/demonstracao_codigo.mp4) (~189 MB) — Apresentação técnica do código, modularização, regras de negócio e boas práticas PEP8.
* [**`demonstracao_sistema.mp4`**](https://github.com/theotavio/sistema-pedal-forte/releases/download/v1.0.0/demonstracao_sistema.mp4) (~133 MB) — Demonstração funcional completa de todas as 12 telas e cálculos em tempo real.

Os vídeos em alta definição estão publicados e disponíveis para download na seção de **[Releases v1.0.0](https://github.com/theotavio/sistema-pedal-forte/releases/tag/v1.0.0)**.

---

## Instruções de Execução

### Pré-requisitos
* Sistema Operacional: Linux (Ubuntu, Debian, Fedora, Arch ou derivados)
* Python 3.10 ou superior
* Bibliotecas: `PySide6`, `matplotlib`

### Instalação das Dependências

Recomenda-se o uso de ambiente virtual (`venv`):

```bash
# Criação do ambiente virtual (opcional)
python3 -m venv .venv
source .venv/bin/activate

# Instalação dos pacotes
pip install PySide6 matplotlib
```

### Inicialização do Sistema

Basta executar o script principal:

```bash
python3 main.py
```

*Ao ser iniciado pela primeira vez, o sistema detecta a ausência de dados e executa automaticamente a população da fábrica fictícia Pedal Forte (bicicletas Mountain Bike aro 29, Urbana Conforto, quadros, rodas, cockpits, componentes e centros produtivos).*

---

## Instruções de Uso

1. **Painel Geral (Dashboard):**
   * Visualize os 4 cartões de KPIs: total de itens, itens com estoque abaixo do nível de segurança, ordens ativas e centros de trabalho sobrecarregados.
   * Utilize as ações rápidas para navegar diretamente para os módulos ou rodar o MRP.
2. **Cadastro e Gestão de Itens (RF02):**
   * Filtre por tipo (PA, SA, MP) ou busque por descrição/código.
   * Cadastre novos itens respeitando a regra `RN01` (formato `Tipo-Número`).
3. **Estrutura de Produto - BOM (RF03):**
   * Selecione um produto acabado ou semiacabado para inspecionar sua árvore de componentes indentada.
   * Ajuste o multiplicador de quantidade para ver a explosão do lote.
   * Adicione novos componentes; o sistema rejeita violações da regra `RN03` (máximo 3 níveis e ciclos).
4. **Gestão de Estoques e Kardex (RF04 / RF05):**
   * Na aba **Posição Geral**, verifique itens marcados com alerta vermelho de risco de ruptura.
   * Na aba **Kardex**, selecione qualquer item para auditar seu histórico imutável (`RN10`).
   * Clique em **Nova Movimentação** para registrar Entradas, Saídas ou Ajustes; saídas que excedam o saldo atual são bloqueadas (`RN02`).
5. **Centros de Trabalho e Roteiros (RF06):**
   * Cadastre centros com capacidade semanal (h) e custo da hora-máquina.
   * No formulário inferior, amarre os itens fabricados (PA e SA) ao centro responsável e defina o tempo unitário em horas.
6. **Plano Mestre de Produção - MPS (RF07):**
   * Edite diretamente as células das 8 semanas para os produtos acabados.
   * Clique em **Salvar Alterações** para persistir a demanda.
7. **Cálculo MRP e Registro Semanal (RF08 / RF09):**
   * Clique em **Executar Cálculo MRP** para processar a demanda em cascata (`RN04`).
   * Selecione qualquer item para inspecionar sua tabela semanal de 6 linhas (Necessidade Bruta, Recebimentos Programados, Estoque Projetado, Necessidade Líquida, Recebimentos Planejados, Liberações Planejadas).
   * Verifique as mensagens de exceção e ordens atrasadas na tabela inferior (`RN07`).
8. **Gestão de Ordens (RF10 / RF11):**
   * Filtre por status ou tipo de ordem.
   * Selecione ordens planejadas e avance seu status: **Firmar** -> **Liberar**.
   * Para uma OP liberada, clique em **Apontar Produção**: o sistema verifica se há estoque de todos os componentes da BOM. Se faltar qualquer um, rejeita com mensagem detalhada; se houver saldo, consome os insumos e gera o produto final.
   * Para uma OC liberada, clique em **Receber Compra** para creditar a matéria-prima no almoxarifado.
9. **Planejamento de Capacidade - CRP (RF12):**
   * Selecione o centro de trabalho para analisar a carga semanal e a taxa de ocupação percentual.
   * Semanas com sobrecarga são marcadas em vermelho; a tabela inferior lista as OPs que geraram o gargalo.
10. **Custos Padrão (RF13):**
    * Escolha um item fabricado para visualizar os cartões de custo de materiais, custo de mão de obra e custo total.
    * Inspecione o desdobramento analítico de todos os insumos diretos.
11. **Gráficos Gerenciais - Matplotlib (RF16):**
    * Navegue pelas 4 abas gráficas (16.1 Saldo x Segurança, 16.2 Estoque Projetado no MRP, 16.3 Ordens por Entrega, 16.4 Carga x Capacidade no CRP).
    * Clique em **Salvar PNG** para gravar a imagem em alta resolução.
12. **Exportação de Dados (RF14):**
    * Exporte a **Posição Geral de Estoque** e a **Lista Geral de Ordens** em CSV com codificação UTF-8 compatível com Excel e LibreOffice.
