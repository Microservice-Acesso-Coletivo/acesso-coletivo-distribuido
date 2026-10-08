# Acesso Coletivo

Back-end de um aplicativo de tecnologia assistiva para pessoas com deficiência visual no
transporte coletivo de Teresina-PI. O app avisa, por áudio e/ou vibração, quando a pessoa está
chegando perto da parada ou do terminal.

Entrega 2 da disciplina de Desenvolvimento de Sistemas Distribuídos (UNIFAPI). O projeto é só
back-end: uma API e dois microsserviços que conversam entre si de forma síncrona.

## Índice

- [Arquitetura](#arquitetura)
- [As 5 camadas](#as-5-camadas)
- [Requisitos do professor e onde estão no código](#requisitos-do-professor-e-onde-estão-no-código)
- [Como rodar](#como-rodar)
- [Endpoints da acesso_api](#endpoints-da-acesso_api)
- [Tratamento de erros](#tratamento-de-erros)
- [Roteiro de demonstração (15 minutos)](#roteiro-de-demonstração-15-minutos)
- [Como explicar o projeto](#como-explicar-o-projeto)

## Arquitetura

São três serviços independentes. Cada um tem seu próprio processo, sua própria porta e seu
próprio banco SQLite. Eles só se conhecem por HTTP e JSON.

```
                       Cliente (app, Postman, navegador)
                                     |
                                     | HTTP + JSON
                                     v
                   +-----------------------------------+
                   |          acesso_api :8080         |
                   |   porta de entrada do sistema     |
                   |   banco: data/acesso.db           |
                   |   (histórico de alertas)          |
                   +-----------------------------------+
                        |                         |
     (1) síncrona       |                         |   repasse de usuários
     API -> serviço     |                         |   (cadastro, busca, login)
     GET /paradas/alerta|                         |
                        v                         |
   +-------------------------------+              |
   |    transporte_service :8082   |              |
   |    paradas, Haversine e       |              |
   |    nível do alerta            |              |
   |    banco: data/transporte.db  |              |
   +-------------------------------+              |
                        |                         |
     (2) síncrona       |                         |
     serviço -> serviço |                         |
     GET /usuarios/{id} |                         |
                        v                         v
                   +-----------------------------------+
                   |       usuario_service :8081       |
                   |   cadastro, login e preferência   |
                   |   de alerta                       |
                   |   banco: data/usuarios.db         |
                   +-----------------------------------+
```

As duas comunicações síncronas do fluxo de alerta:

1. **API para microsserviço:** a `acesso_api` chama o `transporte_service` e fica esperando a resposta.
2. **Microsserviço para microsserviço:** o `transporte_service` chama o `usuario_service` para saber
   a preferência de alerta do usuário e também fica esperando.

"Síncrona" quer dizer que quem chama para e espera a resposta antes de continuar. As chamadas são
feitas com `httpx` e ficam isoladas na pasta `clients/` de cada serviço.

| Serviço | Porta | Responsabilidade | Banco |
|---|---|---|---|
| `acesso_api` | 8080 | Porta de entrada. Repassa pedidos e guarda o histórico de alertas | `data/acesso.db` |
| `usuario_service` | 8081 | Cadastro, login e preferência de alerta (AUDIO, VIBRACAO, AMBOS) | `data/usuarios.db` |
| `transporte_service` | 8082 | Paradas e terminais, cálculo da parada mais próxima e do nível do alerta | `data/transporte.db` |

Tecnologias: Python 3.10+, FastAPI, Uvicorn, SQLAlchemy 2 com SQLite, Pydantic v2 e httpx.

## As 5 camadas

Os três serviços têm a mesma organização de pastas.

| Camada | O que faz | `usuario_service` | `transporte_service` | `acesso_api` |
|---|---|---|---|---|
| **Model** | Estrutura de dados central, mapeada para a tabela do banco | `models/usuario.py` | `models/parada.py` | `models/historico_alerta.py` |
| **Repository** | Única camada que fala com o banco: CRUD e consultas | `repositories/usuario_repository.py` | `repositories/parada_repository.py` | `repositories/historico_repository.py` |
| **Service** | Regras de negócio, cálculos, conversão entre DTO e Model | `services/usuario_service.py`, `services/senha.py` | `services/parada_service.py`, `services/alerta_service.py`, `services/carga_inicial.py` | `services/usuario_service.py`, `services/parada_service.py`, `services/alerta_service.py` |
| **Controller** | Ponto de entrada HTTP: recebe, chama o Service e devolve o JSON com o status | `controllers/usuario_controller.py` | `controllers/parada_controller.py` | `controllers/usuario_controller.py`, `controllers/parada_controller.py`, `controllers/alerta_controller.py` |
| **DTO** | Contrato do JSON de entrada (request) e de saída (response) | `dtos/usuario_request.py`, `dtos/usuario_response.py` | `dtos/parada_request.py`, `dtos/parada_response.py` | `dtos/request.py`, `dtos/response.py` |

Além das camadas, cada serviço tem:

- `main.py`: cria o app, as tabelas e liga as rotas.
- `database.py`: conexão com o SQLite.
- `exceptions.py`: exceções de domínio e o handler central de erros.
- `clients/` (só em `transporte_service` e `acesso_api`): as chamadas HTTP aos outros serviços.

## Requisitos do professor e onde estão no código

| Requisito | Onde é atendido |
|---|---|
| **Model**: estrutura central mapeada às tabelas | `usuario_service/models/usuario.py` (tabela `usuarios`), `transporte_service/models/parada.py` (tabela `paradas`), `acesso_api/models/historico_alerta.py` (tabela `historico_alertas`) |
| **Repository**: abstrai o banco, CRUD e consultas | `*/repositories/*.py`. Exemplo: `UsuarioRepository.buscar_por_email` e `HistoricoRepository.listar_por_usuario` |
| **Service**: orquestra, calcula, valida regras e converte | Email único e hash da senha em `usuario_service/services/usuario_service.py`; Haversine e nível do alerta em `transporte_service/services/alerta_service.py`; chamar, gravar e devolver em `acesso_api/services/alerta_service.py` |
| **Controller**: entrada HTTP com status code adequado | `*/controllers/*.py`. 201 na criação, 200 nas consultas, 204 na remoção |
| **DTO**: contratos de entrada e saída | `*/dtos/`, com request e response em arquivos separados. A validação dos campos é feita pelo Pydantic |
| Comunicação síncrona **entre API e microsserviço** | `acesso_api/clients/transporte_client.py` e `acesso_api/clients/usuario_client.py`, usando `acesso_api/clients/chamada_http.py` |
| Comunicação síncrona **entre microsserviços** | `transporte_service/clients/usuario_client.py` (o transporte consulta o usuário) |
| Controller nunca fala com o banco | Nenhum controller importa Repository nem sessão: só DTOs e Service |
| Service nunca devolve o Model para fora | Todo método público de Service devolve um DTO de resposta (`_para_response` / `model_validate`) |
| DTO de resposta nunca expõe a senha | `UsuarioResponse` não tem campo de senha. No banco só existe `senha_hash` (PBKDF2 com salt, em `usuario_service/services/senha.py`) |
| Erros padronizados | `*/exceptions.py`: exceções de domínio e um handler central. Corpo sempre `{"status", "erro", "mensagem"}` |
| Serviço fora do ar | Timeout nas chamadas e resposta 503 com mensagem clara (`clients/` de `transporte_service` e `acesso_api`) |

## Como rodar

Pré-requisitos: Windows com PowerShell, Python 3.10 ou mais novo e Git.

```powershell
git clone https://github.com/JoaopedroCODES/acesso-coletivo-distribuido.git
cd acesso-coletivo-distribuido

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\run-all.ps1
```

O `run-all.ps1` sobe os três serviços em background e grava os logs na pasta `logs`. Para derrubar
tudo, use `.\stop-all.ps1`.

Se o PowerShell recusar o script por causa da política de execução, rode assim:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-all.ps1
powershell -ExecutionPolicy Bypass -File .\stop-all.ps1
```

Com tudo no ar, a documentação interativa (Swagger) de cada serviço fica em:

- http://127.0.0.1:8080/docs (acesso_api)
- http://127.0.0.1:8081/docs (usuario_service)
- http://127.0.0.1:8082/docs (transporte_service)

### Subir manualmente

Se preferir ver os logs ao vivo, abra três terminais na raiz do projeto e rode um comando em cada:

```powershell
.\.venv\Scripts\python.exe -m uvicorn usuario_service.main:app --port 8081
.\.venv\Scripts\python.exe -m uvicorn transporte_service.main:app --port 8082
.\.venv\Scripts\python.exe -m uvicorn acesso_api.main:app --port 8080
```

### Teste rápido pelo PowerShell

```powershell
$api = 'http://127.0.0.1:8080/api'

# 1. Cadastrar usuário
Invoke-RestMethod -Method Post -Uri "$api/usuarios" -ContentType 'application/json' -Body '{"nome":"Ana Beatriz","email":"ana@email.com","senha":"senha123","preferencia_alerta":"AMBOS"}'

# 2. Listar paradas
Invoke-RestMethod -Uri "$api/paradas"

# 3. Gerar alerta a cerca de 80 metros do Terminal Dirceu
Invoke-RestMethod -Method Post -Uri "$api/alertas" -ContentType 'application/json' -Body '{"usuario_id":1,"latitude":-5.1062,"longitude":-42.7527}'

# 4. Ver o histórico
Invoke-RestMethod -Uri "$api/alertas/historico?usuario_id=1"
```

No Windows PowerShell 5.1 o `Invoke-RestMethod` mostra os acentos trocados (por exemplo `estÃ¡` no
lugar de `está`). É só a exibição do PowerShell 5.1: a resposta está correta em UTF-8, e no Postman
e no `/docs` os acentos aparecem normalmente.

### Coleção Postman

Importe `postman/acesso-coletivo.postman_collection.json` no Postman. As requisições estão na ordem
da demonstração, separadas em duas pastas: "Fluxo de demonstração" (01 a 09) e "Erros" (10 a 16).
A variável `base_url` aponta para `http://127.0.0.1:8080`, e a variável `usuario_id` é preenchida
sozinha depois do cadastro ou do login.

### Configuração e dados

- Os endereços dos serviços podem ser trocados pelas variáveis de ambiente `USUARIO_SERVICE_URL`
  (padrão `http://127.0.0.1:8081`) e `TRANSPORTE_SERVICE_URL` (padrão `http://127.0.0.1:8082`).
- Os bancos ficam na pasta `data`, criada na primeira execução. O `transporte_service` já sobe com
  7 paradas e terminais de Teresina cadastrados.
- As coordenadas e os códigos de linha da carga inicial são aproximados, para demonstração.
- Para recomeçar do zero: `.\stop-all.ps1`, apague a pasta `data` e rode `.\run-all.ps1` de novo.

## Endpoints da acesso_api

| Método | Rota | O que faz | Sucesso |
|---|---|---|---|
| POST | `/api/usuarios` | Cadastra usuário (repassa ao `usuario_service`) | 201 |
| GET | `/api/usuarios/{id}` | Busca usuário (repassa ao `usuario_service`) | 200 |
| POST | `/api/usuarios/login` | Confere email e senha (repassa ao `usuario_service`) | 200 |
| GET | `/api/paradas` | Lista paradas (repassa ao `transporte_service`) | 200 |
| POST | `/api/paradas` | Cadastra parada (repassa ao `transporte_service`) | 201 |
| POST | `/api/alertas` | Gera o alerta em tempo real, grava no histórico e devolve | 201 |
| GET | `/api/alertas/historico?usuario_id=1` | Lista o histórico de alertas do usuário | 200 |

Os microsserviços também têm seus próprios endpoints (`/usuarios` com CRUD completo e login na 8081;
`/paradas` com CRUD completo e `/paradas/alerta` na 8082). Veja no `/docs` de cada um.

### Exemplo de alerta

Pedido:

```json
{ "usuario_id": 1, "latitude": -5.1062, "longitude": -42.7527 }
```

Resposta:

```json
{
  "parada": { "id": 1, "nome": "Terminal Dirceu", "latitude": -5.1069, "longitude": -42.7527, "terminal": true, "linhas": "401,402,610" },
  "distancia_metros": 78,
  "tipo_alerta": "AMBOS",
  "nivel": "DESEMBARQUE",
  "mensagem": "Sua parada, Terminal Dirceu, está a 78 metros. Prepare-se para descer."
}
```

Níveis do alerta, pela distância até a parada mais próxima:

| Distância | Nível |
|---|---|
| até 100 m | `DESEMBARQUE` |
| de 100 m a 300 m | `PROXIMO` |
| acima de 300 m | `LONGE` |

O `tipo_alerta` vem da preferência cadastrada pelo usuário.

## Tratamento de erros

Todo erro de regra de negócio sai no mesmo formato, nos três serviços:

```json
{ "status": 404, "erro": "USUARIO_NAO_ENCONTRADO", "mensagem": "Usuário com id 9999 não encontrado." }
```

| Status | Quando acontece |
|---|---|
| 401 | Email ou senha inválidos no login |
| 404 | Usuário ou parada não encontrados |
| 409 | Email já cadastrado |
| 422 | Dados inválidos. É o formato padrão do FastAPI, gerado pela validação dos DTOs |
| 503 | Um serviço de que a requisição depende está fora do ar ou demorou demais |

Quando um microsserviço responde um erro 4xx, a `acesso_api` repassa o mesmo status e o mesmo corpo.
Por isso um usuário inexistente continua sendo 404 mesmo passando por dois serviços. Se o serviço
não responde, a API devolve 503 e não grava nada no histórico.

## Roteiro de demonstração (15 minutos)

Antes de começar: rode `.\stop-all.ps1`, apague a pasta `data` (para o cadastro começar do zero),
rode `.\run-all.ps1` e abra o Postman com a coleção importada.

| Tempo | O que mostrar | Como |
|---|---|---|
| 0:00 a 2:00 | **O problema e a solução.** Pessoa com deficiência visual no ônibus não vê a parada chegando; o app avisa por áudio e vibração | Falar, com o diagrama da arquitetura na tela |
| 2:00 a 4:00 | **Arquitetura.** Três serviços, três portas, três bancos. As duas comunicações síncronas | Diagrama do README e as três abas `/docs` abertas |
| 4:00 a 6:00 | **As 5 camadas.** Mostrar a árvore de pastas de um serviço e abrir um arquivo de cada camada | Pasta `usuario_service` no editor |
| 6:00 a 8:00 | **Cadastro e login.** A resposta não tem senha; no banco só existe o hash | Postman 01, 02 e 03 |
| 8:00 a 9:00 | **Paradas.** A carga inicial com os terminais de Teresina | Postman 04 e 05 |
| 9:00 a 12:00 | **Alerta, o fluxo principal.** Três posições, três níveis. Mostrar nos logs que uma chamada à API gerou chamadas nos outros dois serviços. Depois o histórico gravado | Postman 06, 07, 08 e 09; arquivos em `logs` |
| 12:00 a 13:30 | **Erros.** 404 que atravessa dois serviços, 422 da validação, 409 e 401 | Postman 10 a 15 |
| 13:30 a 14:30 | **Serviço fora do ar.** Derrubar o `transporte_service` e mostrar o 503 com mensagem clara; o histórico não ganha registro | Comando abaixo e Postman 16 |
| 14:30 a 15:00 | **Fechamento.** Tabela de requisitos do professor | README |

Para derrubar só o `transporte_service` durante a demonstração:

```powershell
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8082 -State Listen).OwningProcess -Force
```

Para subir de novo, rode `.\run-all.ps1`: ele só inicia o que não está no ar.

Para mostrar a comunicação entre os serviços nos logs (os acessos ficam nos arquivos `.log`):

```powershell
Get-Content .\logs\acesso_api.log -Tail 3
Get-Content .\logs\transporte_service.log -Tail 3
Get-Content .\logs\usuario_service.log -Tail 3
```

## Como explicar o projeto

### O papel de cada camada, em uma frase

- **DTO:** o formato do JSON que entra e que sai. É onde os campos são validados.
- **Controller:** a porta HTTP. Recebe o pedido, chama o Service e devolve a resposta com o status.
- **Service:** onde ficam as regras e os cálculos. Decide o que fazer e converte Model em DTO.
- **Repository:** o único que fala com o banco.
- **Model:** a classe que representa uma tabela.
- **Client** (apoio): o único que faz chamada HTTP para outro serviço.

Uma forma de lembrar: o pedido entra pelo **Controller**, já no formato do **DTO**; o **Service**
decide; o **Repository** grava ou busca o **Model**; e a resposta volta como **DTO**.

### O caminho de um POST /api/alertas

O cliente envia `{ "usuario_id": 1, "latitude": -5.1062, "longitude": -42.7527 }`.

**Na acesso_api (porta 8080)**

1. **DTO:** o Pydantic confere o corpo com `AlertaRequest` (`dtos/request.py`). Se a latitude estiver
   fora da faixa, a resposta é 422 e nada mais acontece.
2. **Controller:** `gerar_alerta` em `controllers/alerta_controller.py` recebe o DTO e chama o Service.
3. **Service:** `AlertaService.gerar_alerta` em `services/alerta_service.py` pede o alerta ao
   `TransporteClient`.
4. **Comunicação síncrona 1 (API para microsserviço):** o `TransporteClient` faz
   `GET /paradas/alerta` no `transporte_service` e espera a resposta.

**No transporte_service (porta 8082)**

5. **DTO:** os parâmetros são conferidos com `AlertaRequest` (`dtos/parada_request.py`).
6. **Controller:** `gerar_alerta` em `controllers/parada_controller.py` chama o Service.
7. **Service:** `AlertaService.gerar_alerta` em `services/alerta_service.py` pede o usuário ao
   `UsuarioClient`.
8. **Comunicação síncrona 2 (microsserviço para microsserviço):** o `UsuarioClient` faz
   `GET /usuarios/1` no `usuario_service` e espera a resposta.

**No usuario_service (porta 8081)**

9. **Controller:** `buscar_usuario` em `controllers/usuario_controller.py` chama o Service.
10. **Service:** `UsuarioService.buscar` pede o usuário ao Repository.
11. **Repository:** `UsuarioRepository.buscar_por_id` lê a tabela `usuarios`.
12. **Model:** o banco devolve um objeto `Usuario`.
13. **DTO:** o Service converte o `Usuario` em `UsuarioResponse`, sem a senha, e o Controller
    devolve 200.

**De volta ao transporte_service**

14. **Service:** com a preferência do usuário em mãos, pede as paradas ao Repository.
15. **Repository e Model:** `ParadaRepository.listar` devolve os objetos `Parada`.
16. **Service:** calcula a distância até cada parada com a fórmula de Haversine, escolhe a mais
    próxima, define o nível pela distância e monta a mensagem.
17. **DTO:** monta o `AlertaResponse` e o Controller devolve 200.

**De volta à acesso_api**

18. **Service:** converte a resposta em `AlertaResponse` e monta um `HistoricoAlerta`.
19. **Repository e Model:** `HistoricoRepository.salvar` grava o `HistoricoAlerta` na tabela
    `historico_alertas`.
20. **Controller:** devolve 201 com o alerta para o cliente.

### Perguntas que podem aparecer

- **Por que síncrono?** Porque a API precisa da resposta do transporte para responder ao cliente, e
  o transporte precisa da preferência do usuário para montar o alerta. Cada um espera o outro.
- **E se um serviço cair?** As chamadas têm timeout. Quem chamou recebe um erro de rede, transforma
  em uma exceção de domínio e o cliente recebe 503 com uma mensagem clara, em vez de ficar travado.
- **Por que cada serviço tem seu banco?** Para serem independentes. O histórico guarda só o
  `usuario_id`, sem chave estrangeira, porque o usuário mora no banco de outro serviço.
- **Por que o Controller não acessa o banco direto?** Para cada camada ter uma única
  responsabilidade. Se a regra mudar, mexe-se só no Service; se o banco mudar, só no Repository.
- **Por que DTO se já existe o Model?** O Model tem tudo o que está no banco, inclusive o hash da
  senha. O DTO define só o que pode entrar e o que pode sair.
- **O que é Haversine?** É a fórmula que calcula a distância entre dois pontos usando latitude e
  longitude, levando em conta que a Terra é curva.
