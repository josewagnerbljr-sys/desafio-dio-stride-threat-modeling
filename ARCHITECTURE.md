# Decisões de arquitetura

## Camadas
1. **API** (`app/api`): só HTTP — recebe, valida entrada, converte exceções de domínio em status codes.
2. **Serviços** (`app/services`): regra de negócio. `StrideAnalyzer` orquestra; não conhece FastAPI.
3. **Infra** (`azure_openai_client`, `mock_client`): detalhes de provedor, atrás do `Protocol` `ClienteIA`.
4. **Schemas** (`app/schemas`): contrato único usado para validar a saída da IA e a resposta da API.

## Decisões
| Decisão | Motivo |
|---|---|
| `Protocol ClienteIA` | Troca de provedor sem tocar no analisador; testes sem rede |
| Mock automático sem credenciais | Projeto avaliável e demonstrável sem custo ou conta Azure |
| Validação Pydantic da saída do LLM | LLM devolve texto; só dado validado vira "ameaça" |
| Reparo de JSON + erro de domínio | Robustez contra respostas com markdown; falha explícita quando irrecuperável |
| `temperature=0.2` + `response_format=json_object` | Consistência e JSON válido |
| Retry apenas em erros transitórios | 429/timeout/conexão se recuperam; 4xx de conteúdo não |
| Prompts em módulo próprio | Versionar e testar prompts separadamente da infraestrutura |
| Logs JSON + request_id | Correlação de eventos em Azure Monitor/ELK |
| Container não-root, read-only | Hardening básico de superfície de ataque |

## Limitações conhecidas
- O modo mock devolve um relatório genérico fixo; não analisa a imagem.
- Rate limit em memória (por processo); em múltiplas réplicas usar Redis.
- API key é adequada a estudo; produção deve usar OAuth2/Azure AD.
- A qualidade da análise real depende da legibilidade do diagrama e do modelo.
