# Ameaças STRIDE — exemplo_diagrama.png

## Resumo da arquitetura

Arquitetura web típica de três camadas: um cliente (navegador/app) se comunica via HTTPS com uma API, que por sua vez consulta um banco de dados. Foi identificada uma fronteira de confiança clara entre a rede pública (cliente) e a rede interna (API e banco de dados).

## Componentes identificados

| Componente | Tipo | Descrição |
|---|---|---|
| Cliente Web/Mobile | ator externo | Usuário final acessando o sistema |
| API Backend | processo | Serviço que expõe endpoints REST/HTTP |
| Banco de Dados | armazenamento de dados | Persistência de dados da aplicação |

## Visão geral

| Categoria STRIDE | Ameaças |
|---|:-:|
| Spoofing | 1 |
| Tampering | 1 |
| Repudiation | 1 |
| Information Disclosure | 1 |
| Denial of Service | 1 |
| Elevation of Privilege | 1 |

| Severidade | Ameaças |
|---|:-:|
| 🟢 Baixa | 0 |
| 🟡 Média | 2 |
| 🟠 Alta | 3 |
| 🔴 Crítica | 1 |

## Ameaças (da mais crítica para a menos crítica)

### 1. 🔴 Exposição de dados sensíveis em repouso

- **Categoria:** Information Disclosure
- **Componente afetado:** Banco de Dados
- **Severidade:** Crítica

Dados sensíveis armazenados sem criptografia podem vazar em caso de acesso não autorizado ao disco.

**Mitigações recomendadas:**
- Habilitar criptografia em repouso (TDE) no banco de dados
- Mascarar/tokenizar campos sensíveis (PII) na camada de aplicação

### 2. 🟠 Ausência de autenticação forte no endpoint público

- **Categoria:** Spoofing
- **Componente afetado:** API Backend
- **Severidade:** Alta

Se a API não exigir um mecanismo de autenticação robusto (ex.: OAuth2/JWT com assinatura válida), um atacante pode se passar por um usuário legítimo.

**Mitigações recomendadas:**
- Implementar OAuth2 com tokens JWT assinados e de curta duração
- Exigir MFA para operações sensíveis

### 3. 🟠 Adulteração de dados em trânsito

- **Categoria:** Tampering
- **Componente afetado:** Fluxo Cliente → API
- **Severidade:** Alta

Sem TLS obrigatório, um atacante posicionado na rede pode interceptar e alterar requisições.

**Mitigações recomendadas:**
- Forçar HTTPS/TLS 1.2+ em todos os endpoints (HSTS)
- Validar integridade da requisição com assinatura HMAC quando aplicável

### 4. 🟠 Controle de acesso insuficiente entre papéis (RBAC)

- **Categoria:** Elevation of Privilege
- **Componente afetado:** API Backend
- **Severidade:** Alta

Sem validação de autorização por recurso, um usuário comum pode acessar funções administrativas.

**Mitigações recomendadas:**
- Implementar RBAC/ABAC com verificação de permissão em cada endpoint
- Aplicar o princípio do menor privilégio nas credenciais de acesso ao banco de dados

### 5. 🟡 Falta de trilha de auditoria para operações críticas

- **Categoria:** Repudiation
- **Componente afetado:** API Backend
- **Severidade:** Média

Sem logs de auditoria assinados, um usuário pode negar ter executado uma ação no sistema.

**Mitigações recomendadas:**
- Registrar logs de auditoria imutáveis (write-once) com timestamp e identidade do ator
- Centralizar logs em um SIEM com retenção mínima definida por política

### 6. 🟡 Ausência de limitação de taxa (rate limiting)

- **Categoria:** Denial of Service
- **Componente afetado:** API Backend
- **Severidade:** Média

Sem rate limiting, a API fica vulnerável a ataques de força bruta e sobrecarga volumétrica.

**Mitigações recomendadas:**
- Aplicar rate limiting por IP/API key (ex.: token bucket)
- Colocar a API atrás de um WAF/CDN com proteção anti-DDoS
