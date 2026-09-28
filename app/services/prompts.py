"""
Prompt engineering para análise de ameaças STRIDE a partir de diagramas de
arquitetura.

Manter os prompts num módulo próprio (em vez de strings soltas dentro do
cliente de IA) permite versioná-los, testá-los isoladamente e trocar de
estratégia (few-shot, chain-of-thought, structured outputs) sem tocar na
lógica de infraestrutura.
"""

from app.schemas.threat_model import RelatorioSTRIDE

# Schema JSON explícito injetado no prompt. Modelos multimodais seguem
# instruções de formato com muito mais fidelidade quando recebem o
# "shape" exato esperado, em vez de apenas uma descrição em prosa.
_SCHEMA_JSON_EXEMPLO = RelatorioSTRIDE.model_json_schema()

PROMPT_SISTEMA = """\
Você é um Arquiteto de Segurança Sênior especializado em Threat Modeling, \
com profundo domínio da metodologia STRIDE (Spoofing, Tampering, \
Repudiation, Information Disclosure, Denial of Service, Elevation of \
Privilege), criada pela Microsoft.

Sua tarefa: analisar a imagem de um diagrama de arquitetura de software e \
produzir um relatório de ameaças de segurança estruturado.

Metodologia a seguir (raciocine internamente nesta ordem, mas responda \
apenas com o JSON final, sem incluir esse raciocínio na saída):

1. Identifique todos os componentes do diagrama: processos (ex.: serviços, \
   APIs), armazenamentos de dados (ex.: bancos de dados, filas), atores \
   externos (ex.: usuários, sistemas terceiros) e os fluxos de dados/setas \
   que os conectam.
2. Para cada elemento e cada fronteira de confiança (trust boundary) \
   visível no diagrama, avalie sistematicamente as seis categorias STRIDE:
   - Spoofing: alguém pode se passar por outra identidade?
   - Tampering: dados ou código podem ser adulterados indevidamente?
   - Repudiation: uma ação pode ser executada sem deixar rastro auditável?
   - Information Disclosure: dados sensíveis podem vazar ou ser expostos?
   - Denial of Service: o componente pode ser sobrecarregado ou derrubado?
   - Elevation of Privilege: alguém pode obter permissões além das \
     concedidas?
3. Para cada ameaça identificada, atribua uma severidade (Baixa, Média, \
   Alta ou Crítica) considerando impacto e probabilidade de exploração, e \
   sugira de 1 a 3 mitigações técnicas concretas e acionáveis (não \
   genéricas como apenas "usar criptografia" — especifique como).
4. Priorize qualidade sobre quantidade: é preferível reportar 8 a 15 \
   ameaças bem fundamentadas e específicas ao diagrama do que uma lista \
   longa de itens genéricos que se aplicariam a qualquer sistema.

Responda ESTRITAMENTE em JSON válido, sem markdown, sem texto antes ou \
depois, seguindo exatamente este schema:

{schema}
"""

PROMPT_USUARIO_PADRAO = """\
Analise o diagrama de arquitetura na imagem em anexo e gere o relatório de \
ameaças STRIDE completo, no formato JSON especificado nas instruções de \
sistema. Considere o diagrama como um sistema em produção, exposto à \
internet, salvo indicação contrária visível no próprio diagrama.
"""


def construir_prompt_sistema() -> str:
    return PROMPT_SISTEMA.format(schema=_SCHEMA_JSON_EXEMPLO)


def construir_mensagens(prompt_usuario: str | None, imagem_base64: str, mime_type: str) -> list[dict]:
    """
    Monta a lista de mensagens no formato esperado pela API de Chat
    Completions multimodal (compatível com Azure OpenAI GPT-4o/GPT-4-Vision).
    """
    return [
        {"role": "system", "content": construir_prompt_sistema()},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_usuario or PROMPT_USUARIO_PADRAO},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{imagem_base64}"},
                },
            ],
        },
    ]
