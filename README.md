# Acesso Coletivo

Back-end de um aplicativo de tecnologia assistiva para pessoas com deficiência visual no
transporte coletivo de Teresina-PI. O app avisa, por áudio e/ou vibração, quando a pessoa está
chegando perto da parada ou do terminal.

Entrega 3 da disciplina de Desenvolvimento de Sistemas Distribuídos (UNIFAPI). O projeto é só
back-end: uma API e dois microsserviços. Na Entrega 2 eles conversavam só por HTTP (síncrono). Na
Entrega 3 o fluxo do alerta passou a ser **assíncrono, baseado em eventos**, com o **RabbitMQ**
como Message Broker.

## Índice

[#índice](#índice)

- [Arquitetura](#arquitetura)
- [Fluxo assíncrono do alerta](#fluxo-assíncrono-do-alerta)
- [RabbitMQ: exchange, filas e chaves](#rabbitmq-exchange-filas-e-chaves)
- [As 5 camadas](#as-5-camadas)
- [Requisitos do professor e onde estão no código](#requisitos-do-professor-e-onde-est%C3%A3o-no-c%C3%B3digo)
- [Como rodar](#como-rodar)
- [Endpoints da acesso_api](#endpoints-da-acesso_api)
- [Tratamento de erros](#tratamento-de-erros)
- [Resiliência e limitações](#resili%C3%AAncia-e-limita%C3%A7%C3%B5es)
- [Roteiro de demonstração (15 minutos)](#roteiro-de-demonstra%C3%A7%C3%A3o-15-minutos)
- [Como explicar o projeto](#como-explicar-o-projeto)

## Arquitetura

[#arquitetura](#arquitetura)

São três serviços independentes e um broker. Cada serviço tem seu próprio processo, sua própria
porta e seu próprio banco SQLite. Para o fluxo do alerta eles não se chamam mais: só publicam e
consomem eventos no RabbitMQ.

```
                     Cliente (app, Postman, navegador)
                                   |
                                   | POST /api/alertas   ->   202 Accepted
                                   v
                 +-----------------------------------+
                 |          acesso_api :8080         |
                 |  salva o pedido (PENDENTE)        |
                 |  banco: data/acesso.db            |
                 +-----------------------------------+
                      |                        ^
      (1) publica     |                        |  (4) consome
      alerta.solicitado                        |  alerta.gerado ou alerta.falhou
                      v                        |  (fila acesso.alerta-concluido)
        +----------------------------------------------------+
        |            RabbitMQ  (exchange acesso.eventos)     |
        +----------------------------------------------------+
           |                                   ^        |
           | (2) fila                          |        | (4) alerta.gerado: uma copia
           | transporte.alerta-solicitado      |        |     para cada fila assinante
           v                                   |        v
 +-------------------------------+   (3) publica   +-------------------------------+
 |    transporte_service :8082   |   alerta.gerado |      usuario_service :8081    |
 |  Haversine e nivel do alerta  |   ou falhou     |  atividade de alertas do      |
 |  banco: data/transporte.db    |                 |  usuario (fila                |
 +-------------------------------+                 |  usuario.alerta-gerado)       |
           |                                       |  banco: data/usuarios.db      |
           |  GET /usuarios/{id}                   +-------------------------------+
           |  (HTTP sincrona, continua)                         ^
           +----------------------------------------------------+
```

O que mudou e o que continua síncrono:

| Comunicação                                              | Entrega 2           | Entrega 3                                      |
| -------------------------------------------------------- | ------------------- | ---------------------------------------------- |
| `acesso_api` pede o alerta ao `transporte_service`       | HTTP síncrono       | **Evento** `alerta.solicitado` (assíncrono)    |
| Resultado do alerta volta para a `acesso_api` (histórico)| Resposta do HTTP    | **Evento** `alerta.gerado` / `alerta.falhou`   |
| `usuario_service` fica sabendo dos alertas do usuário    | Não existia         | **Evento** `alerta.gerado` (Publish/Subscribe) |
| `transporte_service` busca a preferência do usuário      | HTTP síncrono       | HTTP síncrono (mantido de propósito)           |
| Cadastro, login, paradas (CRUD)                          | HTTP síncrono       | HTTP síncrono (o cliente precisa da resposta)  |

A chamada do transporte ao usuário continua síncrona porque o cálculo precisa da preferência de
alerta para seguir. Ela agora acontece dentro do consumidor, longe da requisição do cliente.

| Serviço              | Porta | Responsabilidade                                                                          | Banco                |
| -------------------- | ----- | ----------------------------------------------------------------------------------------- | -------------------- |
| `acesso_api`         | 8080  | Porta de entrada. Aceita o pedido de alerta (202), acompanha o andamento e guarda histórico | `data/acesso.db`     |
| `usuario_service`    | 8081  | Cadastro, login, preferência de alerta e resumo de atividade de alertas                   | `data/usuarios.db`   |
| `transporte_service` | 8082  | Paradas e terminais, parada mais próxima e nível do alerta                                | `data/transporte.db` |
| RabbitMQ             | 5672  | Message Broker (painel de administração em 15672)                                         | volume do Docker     |

Tecnologias: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy 2 com SQLite, Pydantic v2, httpx e
**pika** (cliente do RabbitMQ). O broker roda em Docker (`docker-compose.yml`).

## Fluxo assíncrono do alerta

[#fluxo-assíncrono-do-alerta](#fluxo-assíncrono-do-alerta)

Por que este fluxo: o app precisa de uma resposta imediata ("seu pedido foi recebido"), mas o
cálculo final (achar a parada, consultar o usuário) pode acontecer logo depois. Se o
`transporte_service` estiver lento ou fora do ar, a API continua aceitando pedidos.

1. **Produtor (`acesso_api`)**. O Controller recebe `POST /api/alertas`. O Service salva o pedido
   no banco da API com status `PENDENTE`, serializa um `AlertaSolicitadoEvent` e publica na exchange
   com a chave `alerta.solicitado`. O Controller devolve **202 Accepted** com o `solicitacao_id`.
   O produtor não sabe quem vai consumir.
2. **Consumidor (`transporte_service`)**. O Consumer escuta a fila `transporte.alerta-solicitado`,
   desserializa a mensagem para o DTO e aciona o `AlertaService`, que reaproveita o mesmo cálculo
   do endpoint HTTP (Haversine e nível).
3. **Resultado**. O `transporte_service` publica `alerta.gerado`. Se o usuário não existe (erro de
   negócio), publica `alerta.falhou` em vez de tentar de novo.
4. **Assinantes (Publish/Subscribe)**. O evento `alerta.gerado` chega a duas filas, uma cópia para
   cada assinante: a `acesso_api` (marca a solicitação `CONCLUIDA` e grava o histórico) e o
   `usuario_service` (atualiza o total e o último alerta do usuário).
5. **Cliente**. Consulta `GET /api/alertas/{solicitacao_id}` e vê `PENDENTE`, `CONCLUIDA` (com o
   alerta) ou `FALHOU` (com o motivo).

## RabbitMQ: exchange, filas e chaves

[#rabbitmq-exchange-filas-e-chaves](#rabbitmq-exchange-filas-e-chaves)

Uma exchange do tipo **topic** (`acesso.eventos`). Quem publica só informa a chave de roteamento; o
broker entrega para toda fila ligada àquela chave.

| Fila                            | Chaves ligadas                         | Consumidor           | Padrão                     |
| ------------------------------- | -------------------------------------- | -------------------- | -------------------------- |
| `transporte.alerta-solicitado`  | `alerta.solicitado`                    | `transporte_service` | Point-to-Point (fila única)|
| `acesso.alerta-concluido`       | `alerta.gerado`, `alerta.falhou`       | `acesso_api`         | Pub/Sub (assinante 1)      |
| `usuario.alerta-gerado`         | `alerta.gerado`                        | `usuario_service`    | Pub/Sub (assinante 2)      |

Padrões usados:

- **Point-to-Point**: a fila `transporte.alerta-solicitado` entrega cada mensagem a **uma só**
  instância. Se subirem duas instâncias do `transporte_service`, elas dividem o trabalho
  (balanceamento de carga).
- **Publish/Subscribe**: `alerta.gerado` é publicado uma vez e o broker faz uma cópia para cada fila
  assinante. O `transporte_service` não sabe que existem dois interessados.

Garantias e proteções:

| Recurso                  | O que faz                                                                                       |
| ------------------------ | ----------------------------------------------------------------------------------------------- |
| Filas e mensagens duráveis | Sobrevivem a um restart do RabbitMQ (`durable` e `delivery_mode=2`)                           |
| Confirmação do publisher | A API só responde 202 depois de o broker confirmar o recebimento                                |
| Ack manual               | A mensagem só sai da fila depois de processada. Se o consumidor cair no meio, ela volta         |
| Retentativas             | Falha temporária (ex: `usuario_service` fora do ar): 3 tentativas com espera de 1s e 2s         |
| DLQ (fila morta)         | Esgotadas as tentativas, ou mensagem inválida, a mensagem vai para `<fila>.dlq` e não se perde  |
| Idempotência             | Mensagem repetida é ignorada (status da solicitação e `evento_id`)                              |

### Eventos (DTOs de mensagem)

Todo evento tem `evento_id` (UUID) e `ocorrido_em`. Ficam em `messaging/eventos.py` de cada serviço
(cada um tem a sua cópia do contrato, sem compartilhar código).

| Evento                  | Chave               | Publicado por        | Campos principais                                                         |
| ----------------------- | ------------------- | -------------------- | ------------------------------------------------------------------------- |
| `AlertaSolicitadoEvent` | `alerta.solicitado` | `acesso_api`         | `solicitacao_id`, `usuario_id`, `latitude`, `longitude`                   |
| `AlertaGeradoEvent`     | `alerta.gerado`     | `transporte_service` | `solicitacao_id`, `usuario_id`, `parada_nome`, `distancia_metros`, `nivel`, `tipo_alerta`, `mensagem` |
| `AlertaFalhouEvent`     | `alerta.falhou`     | `transporte_service` | `solicitacao_id`, `usuario_id`, `codigo`, `motivo`                        |

## As 5 camadas

Os três serviços têm a mesma organização de pastas.

| Camada | O que faz | `usuario_service` | `transporte_service` | `acesso_api` |
|---|---|---|---|---|
| **Model** | Estrutura de dados central, mapeada para a tabela do banco | `models/usuario.py`, `models/atividade_alerta.py` | `models/parada.py` | `models/historico_alerta.py`, `models/solicitacao_alerta.py` |
| **Repository** | Única camada que fala com o banco: CRUD e consultas | `repositories/usuario_repository.py`, `repositories/atividade_repository.py` | `repositories/parada_repository.py` | `repositories/historico_repository.py`, `repositories/solicitacao_repository.py` |
| **Service** | Regras de negócio, cálculos, conversão entre DTO e Model | `services/usuario_service.py`, `services/atividade_service.py`, `services/senha.py` | `services/parada_service.py`, `services/alerta_service.py`, `services/carga_inicial.py` | `services/usuario_service.py`, `services/parada_service.py`, `services/alerta_service.py` |
| **Controller** | Ponto de entrada HTTP: recebe, chama o Service e devolve o JSON com o status | `controllers/usuario_controller.py`, `controllers/atividade_controller.py` | `controllers/parada_controller.py` | `controllers/usuario_controller.py`, `controllers/parada_controller.py`, `controllers/alerta_controller.py` |
| **DTO** | Contrato do JSON de entrada (request) e de saída (response) | `dtos/usuario_request.py`, `dtos/usuario_response.py`, `dtos/atividade_response.py` | `dtos/parada_request.py`, `dtos/parada_response.py` | `dtos/request.py`, `dtos/response.py` |

Além das camadas, cada serviço tem:

- `main.py`: cria o app, as tabelas e liga as rotas.
- `database.py`: conexão com o SQLite.
- `exceptions.py`: exceções de domínio e o handler central de erros.
- `clients/` (só em `transporte_service` e `acesso_api`): as chamadas HTTP aos outros serviços.
- `messaging/`: tudo que fala com o RabbitMQ. `broker.py` (endereço, exchange e topologia),
  `eventos.py` (DTOs dos eventos), `publisher.py` (publica; só em `acesso_api` e `transporte_service`)
  e `consumidor.py` (thread que escuta uma fila, com retentativas e DLQ).
- `consumers/`: o componente Consumer de cada serviço. Recebe a mensagem, desserializa para o DTO e
  aciona o Service. Faz o papel que o Controller faz para HTTP, mas para mensagens.

## Requisitos do professor e onde estão no código

[#requisitos-do-professor-e-onde-estão-no-código](#requisitos-do-professor-e-onde-estão-no-código)

### Entrega 3: comunicação assíncrona

| Requisito                                                        | Onde é atendido                                                                                                                                              |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Message Broker** (RabbitMQ)                                    | `docker-compose.yml`. Topologia em `*/messaging/broker.py`                                                                                                   |
| **Produtor**: Controller recebe a requisição REST                | `acesso_api/controllers/alerta_controller.py` (`POST /api/alertas`)                                                                                          |
| Service executa a lógica local (salva no banco A)                | `acesso_api/services/alerta_service.py` (`solicitar_alerta` grava `SolicitacaoAlerta` em `data/acesso.db`)                                                   |
| Service serializa um DTO de evento e envia para a exchange       | `AlertaSolicitadoEvent` em `acesso_api/messaging/eventos.py`, enviado por `acesso_api/messaging/publisher.py`                                                |
| Controller retorna **202 Accepted**                              | `status_code=status.HTTP_202_ACCEPTED` em `alerta_controller.py`                                                                                             |
| Produtor **não sabe quem é o consumidor**                        | O Service só informa a chave `alerta.solicitado`. Nenhum nome de serviço, URL ou fila aparece no código da `acesso_api` ao publicar                          |
| **Consumidor**: componente que escuta uma fila específica        | `transporte_service/consumers/alerta_consumer.py` (fila `transporte.alerta-solicitado`) e `acesso_api/consumers/`, `usuario_service/consumers/`              |
| Desserializa para o DTO e aciona o Service do consumidor         | `AlertaSolicitadoEvent.model_validate_json` e `AlertaService.processar_solicitacao` em `transporte_service/services/alerta_service.py`                        |
| **Point-to-Point** (fila simples)                                | Fila `transporte.alerta-solicitado`: uma mensagem, uma instância do `transporte_service`                                                                     |
| **Publish/Subscribe** (tópicos)                                  | Evento `alerta.gerado` entregue às filas `acesso.alerta-concluido` e `usuario.alerta-gerado`                                                                 |

### Entrega 2: camadas e comunicação síncrona (mantidos)

| Requisito                                              | Onde é atendido                                                                                                                                                                  |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Model**: estrutura central mapeada às tabelas        | `usuario_service/models/usuario.py`, `transporte_service/models/parada.py`, `acesso_api/models/historico_alerta.py` e `solicitacao_alerta.py`, `usuario_service/models/atividade_alerta.py` |
| **Repository**: abstrai o banco, CRUD e consultas      | `*/repositories/*.py`                                                                                                                                                            |
| **Service**: orquestra, calcula, valida e converte     | `*/services/*.py`. Haversine e nível em `transporte_service/services/alerta_service.py`                                                                                          |
| **Controller**: entrada HTTP com status code adequado  | `*/controllers/*.py`. 201 na criação, 202 no pedido de alerta, 200 nas consultas, 204 na remoção                                                                                 |
| **DTO**: contratos de entrada e saída                  | `*/dtos/`, com request e response em arquivos separados. A validação dos campos é feita pelo Pydantic                                                                            |
| Comunicação síncrona entre API e microsserviço         | `acesso_api/clients/` (cadastro, login e paradas continuam por HTTP)                                                                                                             |
| Comunicação síncrona entre microsserviços              | `transporte_service/clients/usuario_client.py` (a preferência do usuário)                                                                                                        |
| Controller nunca fala com o banco; Service nunca devolve o Model | Mantido. Os Consumers também só chamam o Service                                                                                                                       |
| DTO de resposta nunca expõe a senha                    | `UsuarioResponse` não tem campo de senha. No banco só existe `senha_hash`                                                                                                        |
| Erros padronizados                                     | `*/exceptions.py`. Corpo sempre `{"status", "erro", "mensagem"}`                                                                                                                 |

## Como rodar

[#como-rodar](#como-rodar)

Pré-requisitos: Windows com PowerShell, Python 3.10 ou mais novo, Git e **Docker Desktop** (para o
RabbitMQ).

```
git clone https://github.com/Microservice-Acesso-Coletivo/acesso-coletivo-distribuido.git
cd acesso-coletivo-distribuido

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

docker compose up -d
.\run-all.ps1
```

`docker compose up -d` sobe o RabbitMQ. O `run-all.ps1` confere se o broker está na porta 5672, sobe
os três serviços em background e grava os logs na pasta `logs`. Para derrubar tudo, use
`.\stop-all.ps1` e `docker compose down`.

Se o PowerShell recusar o script por causa da política de execução, rode assim:

```
powershell -ExecutionPolicy Bypass -File .\run-all.ps1
powershell -ExecutionPolicy Bypass -File .\stop-all.ps1
```

Com tudo no ar:

- <http://127.0.0.1:8080/docs> (acesso_api)
- <http://127.0.0.1:8081/docs> (usuario_service)
- <http://127.0.0.1:8082/docs> (transporte_service)
- <http://127.0.0.1:15672> (painel do RabbitMQ, usuário `guest`, senha `guest`)

No painel, a aba **Queues** mostra as filas `transporte.alerta-solicitado`, `acesso.alerta-concluido`
e `usuario.alerta-gerado`, cada uma com sua `.dlq`.

### Subir manualmente

[#subir-manualmente](#subir-manualmente)

Se preferir ver os logs ao vivo, suba o broker e abra três terminais na raiz do projeto. Mantenha
esta ordem: os consumidores criam suas filas ao iniciar, e a `acesso_api` deve ser a última.

```
docker compose up -d
.\.venv\Scripts\python.exe -m uvicorn usuario_service.main:app --port 8081
.\.venv\Scripts\python.exe -m uvicorn transporte_service.main:app --port 8082
.\.venv\Scripts\python.exe -m uvicorn acesso_api.main:app --port 8080
```

### Teste rápido pelo PowerShell

[#teste-rápido-pelo-powershell](#teste-rápido-pelo-powershell)

```
$api = 'http://127.0.0.1:8080/api'

# 1. Cadastrar usuário
Invoke-RestMethod -Method Post -Uri "$api/usuarios" -ContentType 'application/json' -Body '{"nome":"Ana Beatriz","email":"ana@email.com","senha":"senha123","preferencia_alerta":"AMBOS"}'

# 2. Pedir um alerta a cerca de 80 metros do Terminal Dirceu (responde 202 na hora)
$pedido = Invoke-RestMethod -Method Post -Uri "$api/alertas" -ContentType 'application/json' -Body '{"usuario_id":1,"latitude":-5.1062,"longitude":-42.7527}'
$pedido

# 3. Consultar o andamento (PENDENTE, depois CONCLUIDA)
Invoke-RestMethod -Uri "$api/alertas/$($pedido.solicitacao_id)"

# 4. Ver o histórico
Invoke-RestMethod -Uri "$api/alertas/historico?usuario_id=1"

# 5. Ver a atividade registrada no usuario_service (o segundo assinante do evento)
Invoke-RestMethod -Uri "http://127.0.0.1:8081/usuarios/1/atividade-alertas"
```

No Windows PowerShell 5.1 o `Invoke-RestMethod` mostra os acentos trocados (por exemplo `estÃ¡` no
lugar de `está`). É só a exibição do PowerShell 5.1: a resposta está correta em UTF-8, e no Postman
e no `/docs` os acentos aparecem normalmente.

### Coleção Postman

[#coleção-postman](#coleção-postman)

Importe `postman/acesso-coletivo.postman_collection.json` no Postman. As requisições estão na ordem
da demonstração, separadas em duas pastas: "Fluxo de demonstração" (01 a 11) e "Erros" (12 a 21).
A variável `base_url` aponta para `http://127.0.0.1:8080`. As variáveis `usuario_id` e
`solicitacao_id` são preenchidas sozinhas depois do cadastro, do login e de cada pedido de alerta.

### Configuração e dados

[#configuração-e-dados](#configuração-e-dados)

- Os endereços podem ser trocados pelas variáveis de ambiente `USUARIO_SERVICE_URL` (padrão `http://127.0.0.1:8081`), `TRANSPORTE_SERVICE_URL` (padrão `http://127.0.0.1:8082`) e `RABBITMQ_URL` (padrão `amqp://guest:guest@127.0.0.1:5672/%2F`).
- Os bancos ficam na pasta `data`, criada na primeira execução. As tabelas novas desta entrega são criadas sozinhas ao subir os serviços, sem perder os dados da Entrega 2. O `transporte_service` já sobe com
7 paradas e terminais de Teresina cadastrados.
- As coordenadas e os códigos de linha da carga inicial são aproximados, para demonstração.
- Para recomeçar do zero: `.\stop-all.ps1`, apague a pasta `data` e rode `.\run-all.ps1` de novo. Para limpar o broker: `docker compose down -v`.

## Endpoints da acesso_api

[#endpoints-da-acesso_api](#endpoints-da-acesso_api)

| Método | Rota                                  | O que faz                                                           | Sucesso |
| ------ | ------------------------------------- | ------------------------------------------------------------------- | ------- |
| POST   | `/api/usuarios`                       | Cadastra usuário (repassa ao `usuario_service`)                     | 201     |
| GET    | `/api/usuarios/{id}`                  | Busca usuário (repassa ao `usuario_service`)                        | 200     |
| POST   | `/api/usuarios/login`                 | Confere email e senha (repassa ao `usuario_service`)                | 200     |
| GET    | `/api/paradas`                        | Lista paradas (repassa ao `transporte_service`)                     | 200     |
| POST   | `/api/paradas`                        | Cadastra parada (repassa ao `transporte_service`)                   | 201     |
| POST   | `/api/alertas`                        | **Pede** um alerta: salva o pedido, publica o evento e responde     | **202** |
| GET    | `/api/alertas/{solicitacao_id}`       | Consulta o andamento do pedido (`PENDENTE`, `CONCLUIDA`, `FALHOU`)  | 200     |
| GET    | `/api/alertas/historico?usuario_id=1` | Lista o histórico de alertas do usuário                             | 200     |

Os microsserviços também têm seus próprios endpoints (`/usuarios` com CRUD completo e login na 8081;
`/paradas` com CRUD completo e `/paradas/alerta` na 8082). O `usuario_service` ganhou
`GET /usuarios/{id}/atividade-alertas`. Veja no `/docs` de cada um.

### Exemplo de alerta (assíncrono)

[#exemplo-de-alerta-assíncrono](#exemplo-de-alerta-assíncrono)

Pedido:

```
{ "usuario_id": 1, "latitude": -5.1062, "longitude": -42.7527 }
```

Resposta imediata (**202 Accepted**):

```
{
  "solicitacao_id": 1,
  "status": "PENDENTE",
  "mensagem": "Pedido de alerta recebido. O cálculo é feito em segundo plano.",
  "consulta": "/api/alertas/1"
}
```

Consulta pouco depois, em `GET /api/alertas/1`:

```
{
  "id": 1,
  "usuario_id": 1,
  "status": "CONCLUIDA",
  "latitude": -5.1062,
  "longitude": -42.7527,
  "parada_nome": "Terminal Dirceu",
  "distancia_metros": 78,
  "nivel": "DESEMBARQUE",
  "tipo_alerta": "AMBOS",
  "mensagem": "Sua parada, Terminal Dirceu, está a 78 metros. Prepare-se para descer.",
  "codigo_erro": null,
  "motivo_falha": null,
  "criado_em": "2026-10-15T10:00:00.000000",
  "atualizado_em": "2026-10-15T10:00:01.000000"
}
```

Níveis do alerta, pela distância até a parada mais próxima:

| Distância        | Nível         |
| ---------------- | ------------- |
| até 100 m        | `DESEMBARQUE` |
| de 100 m a 300 m | `PROXIMO`     |
| acima de 300 m   | `LONGE`       |

O `tipo_alerta` vem da preferência cadastrada pelo usuário.

## Tratamento de erros

[#tratamento-de-erros](#tratamento-de-erros)

Todo erro de regra de negócio sai no mesmo formato, nos três serviços:

```
{ "status": 404, "erro": "USUARIO_NAO_ENCONTRADO", "mensagem": "Usuário com id 9999 não encontrado." }
```

| Status | Quando acontece                                                                |
| ------ | ------------------------------------------------------------------------------ |
| 401    | Email ou senha inválidos no login                                              |
| 404    | Usuário, parada ou solicitação de alerta não encontrados                       |
| 409    | Email já cadastrado                                                            |
| 422    | Dados inválidos. É o formato padrão do FastAPI, gerado pela validação dos DTOs |
| 503    | Um serviço ou o RabbitMQ está fora do ar (`BROKER_INDISPONIVEL` no caso do broker) |

Quando um microsserviço responde um erro 4xx a uma chamada HTTP, a `acesso_api` repassa o mesmo
status e o mesmo corpo.

No fluxo assíncrono o erro de negócio **não volta no 202**. O pedido é aceito e o erro aparece depois,
no andamento da solicitação. Exemplo para um usuário que não existe:

```
GET /api/alertas/2

{
  "id": 2,
  "status": "FALHOU",
  "codigo_erro": "USUARIO_NAO_ENCONTRADO",
  "motivo_falha": "Usuário com id 9999 não encontrado.",
  ...
}
```

Uma solicitação que falhou não entra no histórico: ele só guarda alertas realmente entregues.

## Resiliência e limitações

[#resiliência-e-limitações](#resiliência-e-limitações)

O que o broker traz:

- **`transporte_service` fora do ar**: antes, a API devolvia 503. Agora a API continua respondendo
  202, o pedido espera na fila e é processado quando o serviço voltar (o status fica `PENDENTE`
  nesse intervalo).
- **`usuario_service` fora do ar** durante o cálculo: o consumidor tenta 3 vezes (espera de 1s e 2s).
  Se continuar fora, a mensagem vai para `transporte.alerta-solicitado.dlq`, onde fica guardada e
  pode ser reenviada depois, em vez de se perder.
- **Consumidor cai no meio de uma mensagem**: como o ack é manual, a mensagem volta para a fila.
- **Mensagem repetida**: o broker entrega "pelo menos uma vez". Por isso o processamento é
  idempotente (a solicitação só muda uma vez e o `usuario_service` compara o `evento_id`).

Limitações assumidas (ficam como melhoria futura):

- **Gravar e publicar não são atômicos.** A API grava o pedido no banco e depois publica. Se o
  processo cair entre os dois passos, o pedido fica `PENDENTE` sem evento. A solução de produção é o
  padrão *Transactional Outbox*. Se o broker responder erro na publicação, a API marca `FALHOU` e
  devolve 503.
- A resposta à `acesso_api` depende de ela estar consumindo. Se estiver fora do ar, as mensagens
  ficam na fila `acesso.alerta-concluido` e são aplicadas quando ela voltar.
- O Publisher abre uma conexão por mensagem. Simples e seguro entre threads, mas em produção se
  reaproveitaria a conexão.
- Não há reprocessamento automático da DLQ nem autenticação no RabbitMQ (usuário `guest`, só para
  desenvolvimento local).
- Se a `acesso_api` publicar antes de a fila do consumidor existir (primeira execução, consumidor
  nunca iniciado), a mensagem é descartada pelo broker. Por isso o `run-all.ps1` sobe a API por
  último. Depois da primeira execução as filas duráveis já existem.

## Roteiro de demonstração (15 minutos)

[#roteiro-de-demonstração-15-minutos](#roteiro-de-demonstração-15-minutos)

Use a coleção do Postman e o painel do RabbitMQ (<http://127.0.0.1:15672>) lado a lado.

1. **Contexto (2 min).** O app avisa a pessoa com deficiência visual quando está chegando na parada.
   Na Entrega 2 tudo era HTTP síncrono. Mostre o diagrama da seção Arquitetura.
2. **Infraestrutura (1 min).** `docker compose up -d`, `.\run-all.ps1`. No painel do RabbitMQ, mostre a
   exchange `acesso.eventos` e as três filas, cada uma com sua `.dlq`.
3. **Cadastro (1 min).** Postman 01 (cadastrar usuário). Continua síncrono: o cliente precisa do id.
4. **Fluxo assíncrono (4 min).** Postman 06. A resposta é **202** imediata. Mostre os logs:
   `acesso_api` publicou, `transporte_service` processou, os dois assinantes consumiram. Postman 09
   mostra `CONCLUIDA`. Postman 10 (histórico) e 11 (atividade no `usuario_service`) provam o
   Publish/Subscribe: um evento, duas ações em serviços diferentes. Rode 07 e 08 para ver os outros
   níveis.
5. **Erro de negócio assíncrono (1 min).** Postman 13 e 14: usuário inexistente. O 202 vem igual, e a
   solicitação termina `FALHOU` com o motivo.
6. **Resiliência (3 min).** Derrube só o `transporte_service`:
   `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8082 -State Listen).OwningProcess -Force`.
   Postman 20: continua **202**. No painel, a fila `transporte.alerta-solicitado` mostra 1 mensagem
   esperando. Suba o serviço de novo
   (`.\.venv\Scripts\python.exe -m uvicorn transporte_service.main:app --port 8082`): a mensagem é
   consumida e a solicitação vira `CONCLUIDA`. Compare com a Entrega 2, que daria 503.
7. **Broker fora do ar (1 min).** `docker compose stop`. Postman 21: 503 `BROKER_INDISPONIVEL`.
   `docker compose start` para voltar.
8. **Fechamento (2 min).** Limitações (seção anterior) e o que faria depois: Outbox e reprocessamento
   da DLQ.

## Como explicar o projeto

[#como-explicar-o-projeto](#como-explicar-o-projeto)

Em uma frase: o app pede o alerta e recebe um "aceito" na hora; quem calcula e quem registra o
resultado são serviços diferentes, que só se conhecem por eventos no RabbitMQ.

Perguntas que costumam aparecer:

- **Por que 202 e não 201?** 201 diz "criei o recurso". 202 diz "recebi o pedido e vou processar". O
  alerta ainda não existe quando a API responde.
- **O produtor sabe quem consome?** Não. A `acesso_api` publica `alerta.solicitado` na exchange e
  mais nada. Poderia haver um, dois ou nenhum consumidor sem mudar uma linha dela.
- **Qual a diferença entre Point-to-Point e Pub/Sub aqui?** `alerta.solicitado` vai para uma fila
  com um consumidor: cada pedido é calculado uma vez (e várias instâncias dividem o trabalho).
  `alerta.gerado` vai para duas filas, e cada assinante recebe sua cópia.
- **Por que manter a chamada do transporte ao usuário em HTTP?** O cálculo precisa da preferência
  para continuar. O enunciado pede para substituir algumas chamadas síncronas: as que causavam
  acoplamento temporal no fluxo principal.
- **O que acontece se o consumidor falhar?** Falha temporária: 3 tentativas e depois DLQ. Erro de
  negócio (usuário inexistente): vira o evento `alerta.falhou` e a solicitação fica `FALHOU`. Queda
  do processo: o ack é manual, então a mensagem volta para a fila.
- **O que é a DLQ?** Fila onde ficam as mensagens que não puderam ser processadas, para análise e
  reenvio, em vez de serem perdidas ou travarem a fila principal.
- **Por que o processamento é idempotente?** O broker entrega "pelo menos uma vez". Sem isso, uma
  mensagem repetida gravaria o histórico duas vezes.
- **Qual o ponto fraco?** Gravar no banco e publicar não são uma operação só (dual write). A solução
  é o Transactional Outbox, citado como melhoria futura.
