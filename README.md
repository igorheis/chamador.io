# Chamador Odontológico

Sistema web para comunicação de chamados entre consultórios odontológicos e auxiliares. Cada solicitação é salva como um registro próprio em SQLite e publicada imediatamente aos painéis conectados por WebSocket.

## Requisitos

- Python 3.10 ou superior
- Navegador moderno

## Instalação

Na pasta do projeto, crie e ative o ambiente virtual e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Inicialização

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Abra `http://localhost:8000`. O banco `database/chamador.db` e os dez consultórios são criados automaticamente na primeira execução. Para acessar em outros dispositivos da mesma rede, use o endereço IP do computador servidor, por exemplo `http://192.168.0.20:8000`.

## Telas

- Início e seleção dos consultórios: `http://localhost:8000/`
- Tela do consultório: selecione uma sala ou abra `/consultorio/1` até `/consultorio/10`
- Painel das auxiliares: `http://localhost:8000/painel`
- Histórico e indicadores: `http://localhost:8000/historico`

No painel, escolha a identificação de auxiliar antes de assumir um chamado. Há cinco auxiliares de demonstração, criadas automaticamente como Auxiliar 01 a 05. O som começa habilitado; se o navegador bloquear o primeiro alerta, interaja uma vez com o painel. A preferência de som e a identificação ficam guardadas naquele navegador.

O dentista pode concluir cada chamado individualmente na tela de seu consultório. A conclusão remove apenas aquele chamado do painel ativo e preserva o registro no histórico.

## Como testar

```bash
python -m unittest discover -s tests -v
```

Os testes exercitam solicitações simultâneas em várias salas, múltiplos chamados em uma única sala, conclusão independente, persistência no histórico e eventos WebSocket de criação, atendimento e conclusão.

## Estrutura

```text
backend/       API, modelos, acesso ao banco, esquemas e regras de chamados
database/      Banco SQLite gerado em execução
templates/     Páginas HTML
static/css/    Estilos responsivos e componentes visuais
static/js/     Interface, WebSocket, som e chamadas à API
tests/         Testes do fluxo de chamados
```

## Próximas melhorias

- Login e permissões por papel para dentistas e auxiliares
- PostgreSQL e publicação com múltiplas instâncias usando um broker de eventos
- Filtros por período, exportação e gráficos de indicadores
- Configuração de nomes das auxiliares pela interface
