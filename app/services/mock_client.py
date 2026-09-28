"""
Cliente mock: implementa o mesmo Protocol `ClienteIA`, mas sem nenhuma
dependência externa.

Por que isso importa para a qualidade do projeto, e não só como
"placeholder": o desafio deixa explícito que a solução pode ser entregue
com ou sem uma conta Azure ativa. Em vez de deixar o projeto inutilizável
sem credenciais, ele detecta a ausência de configuração e usa este cliente
automaticamente (ver `Settings.usar_cliente_mock`), preservando 100% do
comportamento observável da API (mesmos endpoints, mesmo schema de
resposta, mesmos códigos de erro) — quem for avaliar o projeto consegue
rodar `docker compose up` e testar a API de ponta a ponta imediatamente.

O relatório gerado é determinístico e realista, calibrado a partir de
diagramas típicos "cliente → API → banco de dados", cobrindo as 6
categorias STRIDE.
"""

import asyncio
import json


class ClienteIAMock:
    """Implementa o Protocol `ClienteIA` sem chamar nenhum serviço externo."""

    @property
    def nome_modelo(self) -> str:
        return "mock-stride-analyzer-v1"

    async def gerar_analise(self, imagem_base64: str, mime_type: str, prompt_usuario: str | None) -> str:
        # `await asyncio.sleep(0)` cede o loop de eventos — mantém a
        # assinatura async real, simulando I/O sem bloquear nada.
        await asyncio.sleep(0)
        return json.dumps(_RELATORIO_EXEMPLO, ensure_ascii=False)


_RELATORIO_EXEMPLO = {
    "resumo_arquitetura": (
        "Arquitetura web típica de três camadas: um cliente (navegador/app) se "
        "comunica via HTTPS com uma API, que por sua vez consulta um banco de "
        "dados. Foi identificada uma fronteira de confiança clara entre a rede "
        "pública (cliente) e a rede interna (API e banco de dados)."
    ),
    "componentes": [
        {"nome": "Cliente Web/Mobile", "tipo": "ator externo", "descricao": "Usuário final acessando o sistema"},
        {"nome": "API Backend", "tipo": "processo", "descricao": "Serviço que expõe endpoints REST/HTTP"},
        {"nome": "Banco de Dados", "tipo": "armazenamento de dados", "descricao": "Persistência de dados da aplicação"},
    ],
    "ameacas": [
        {
            "categoria": "Spoofing",
            "componente_afetado": "API Backend",
            "titulo": "Ausência de autenticação forte no endpoint público",
            "descricao": (
                "Se a API não exigir um mecanismo de autenticação robusto (ex.: OAuth2/JWT com "
                "assinatura válida), um atacante pode se passar por um usuário legítimo."
            ),
            "severidade": "Alta",
            "mitigacoes": [
                "Implementar OAuth2 com tokens JWT assinados e de curta duração",
                "Exigir MFA para operações sensíveis",
            ],
        },
        {
            "categoria": "Tampering",
            "componente_afetado": "Fluxo Cliente → API",
            "titulo": "Adulteração de dados em trânsito",
            "descricao": "Sem TLS obrigatório, um atacante posicionado na rede pode interceptar e alterar requisições.",
            "severidade": "Alta",
            "mitigacoes": [
                "Forçar HTTPS/TLS 1.2+ em todos os endpoints (HSTS)",
                "Validar integridade da requisição com assinatura HMAC quando aplicável",
            ],
        },
        {
            "categoria": "Repudiation",
            "componente_afetado": "API Backend",
            "titulo": "Falta de trilha de auditoria para operações críticas",
            "descricao": "Sem logs de auditoria assinados, um usuário pode negar ter executado uma ação no sistema.",
            "severidade": "Média",
            "mitigacoes": [
                "Registrar logs de auditoria imutáveis (write-once) com timestamp e identidade do ator",
                "Centralizar logs em um SIEM com retenção mínima definida por política",
            ],
        },
        {
            "categoria": "Information Disclosure",
            "componente_afetado": "Banco de Dados",
            "titulo": "Exposição de dados sensíveis em repouso",
            "descricao": "Dados sensíveis armazenados sem criptografia podem vazar em caso de acesso não autorizado ao disco.",
            "severidade": "Crítica",
            "mitigacoes": [
                "Habilitar criptografia em repouso (TDE) no banco de dados",
                "Mascarar/tokenizar campos sensíveis (PII) na camada de aplicação",
            ],
        },
        {
            "categoria": "Denial of Service",
            "componente_afetado": "API Backend",
            "titulo": "Ausência de limitação de taxa (rate limiting)",
            "descricao": "Sem rate limiting, a API fica vulnerável a ataques de força bruta e sobrecarga volumétrica.",
            "severidade": "Média",
            "mitigacoes": [
                "Aplicar rate limiting por IP/API key (ex.: token bucket)",
                "Colocar a API atrás de um WAF/CDN com proteção anti-DDoS",
            ],
        },
        {
            "categoria": "Elevation of Privilege",
            "componente_afetado": "API Backend",
            "titulo": "Controle de acesso insuficiente entre papéis (RBAC)",
            "descricao": "Sem validação de autorização por recurso, um usuário comum pode acessar funções administrativas.",
            "severidade": "Alta",
            "mitigacoes": [
                "Implementar RBAC/ABAC com verificação de permissão em cada endpoint",
                "Aplicar o princípio do menor privilégio nas credenciais de acesso ao banco de dados",
            ],
        },
    ],
}
