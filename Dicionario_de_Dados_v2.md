# Challenge - AIOps — Dicionário de Dados (v2)

> Convertido para Markdown a partir do arquivo original `Dicionário de Dados - v2.docx`
> fornecido pela Locaweb/FIAP, para facilitar a leitura junto ao código-fonte.
> O arquivo original em `.docx` continua sendo a fonte oficial.

| Nome do Campo | Descrição | Tipo de Dado | Formato / Restrições | Obrigatoriedade | Lista de Valores |
|---|---|---|---|---|---|
| **Número** | Identificador único e sequencial do incidente. | Texto | `INCXXXXXXX` onde XXXXXXX é um número sequencial | Sim | N/A |
| **Prioridade** | Nível de urgência e impacto do incidente. | Texto | `X - aaaaaaa`; somente as prioridades 1, 2 e 3 entram para o KPI | Sim | 1 - Crítica, 2 - Alta, 3 - Média, 4 - Baixa, 5 - Muito Baixa |
| **Produto** | O produto ou serviço afetado pelo incidente. | Texto | N/A | Não | N/A |
| **Categoria** | Classificação primária do tipo de incidente. | Texto | N/A | Não | N/A |
| **Subcategoria** | Classificação secundária, refinando a Categoria. | Texto | Depende de uma Categoria selecionada | Não | N/A |
| **Grupo designado** | Equipe responsável por trabalhar na solução do incidente. | Texto | N/A | Sim | N/A |
| **Item de configuração** | O ativo de TI específico com o problema. | Texto | N/A | Não | N/A |
| **Aberto** | Data e hora exatas em que o incidente foi registrado. | Data/Hora | `dd/mm/aaaa hh:mm:ss` | Sim | N/A |
| **Resolvido** | Data e hora em que a equipe determinou que o incidente foi corrigido. | Data/Hora | `dd/mm/aaaa hh:mm:ss` | Não | N/A |
| **Encerrado** | Data e hora em que o incidente é finalizado. | Data/Hora | `dd/mm/aaaa hh:mm:ss` | Sim | N/A |
| **Duração** | Tempo total entre abertura e resolução/encerramento. | Numérico | Tempo em segundos | Sim | N/A |
| **Código de fechamento** | Razão formal para o encerramento. | Texto | N/A | Não | N/A |
| **Descrição resumida** | Título conciso do incidente. | Texto | N/A | Sim | N/A |
| **Solução** | Informa se a solução foi definitiva, contorno ou nenhuma. | Texto | N/A | Não | Contorno, Definitiva, (em branco) |
| **Aberto por** | Origem da abertura do incidente. | Texto | N/A | Sim | Manual, Monitoramento |
| **Incidente Pai** | Referência a um incidente anterior relacionado/duplicado. | Texto | `INCXXXXXXX` | Não | N/A |
| **Status** | Ponto atual do incidente no ciclo de vida. | Texto | N/A | Sim | Aguardando Problema, Encerrado, Encerrado Automaticamente, Sem Intervenção |
| **Entrou para KPI?** | Se o incidente deve ser considerado no cálculo dos KPIs. | Booleano | SIM / NAO | Sim | N/A |
| **KPI Violado?** | Se o tempo de solução excedeu o limite do SLA. | Booleano | SIM / NAO | Sim | N/A |

## Informações importantes

**Campo Status: "Sem Intervenção"** — a maioria dos incidentes fechados assim está associada ao campo `Aberto por = "Monitoramento"`.

**KPIs medidos** para incidentes com prioridades 1-Crítica, 2-Alta e 3-Média, com base no campo Duração:

| Prioridade | Duração máxima |
|---|---|
| 1 - Crítica | até 4h |
| 2 - Alta | até 4h |
| 3 - Média | até 12h |
| 4 - Baixa | até 24h |
| 5 - Muito Baixa | até 96h |

Chamados com `Incidente Pai` preenchido, ou `Status = "Sem Intervenção"`, **não entram** no cálculo do KPI (mas podem ainda impactar outro incidente que entrou no KPI).

## Metas anuais de KPI (indicador medido mensalmente)

**Incidentes com OLA quebrado no ano:**

| Prioridade | Quantidade | % de atingimento |
|---|---|---|
| 2 - Alta | < 31 | 150% |
| 2 - Alta | 31–35 | 125% |
| 2 - Alta | 36–39 | 100% |
| 2 - Alta | 40–45 | 75% |
| 2 - Alta | 46–53 | 50% |
| 2 - Alta | > 53 | 0% |
| 3 - Média | < 201 | 150% |
| 3 - Média | 201–230 | 125% |
| 3 - Média | 231–263 | 100% |
| 3 - Média | 264–290 | 75% |
| 3 - Média | 291–320 | 50% |
| 3 - Média | > 320 | 0% |

**Volume total de incidentes tratados no ano:**

| Prioridade | Quantidade | % de atingimento |
|---|---|---|
| 2 - Alta | < 4585 | 150% |
| 2 - Alta | 4585–5388 | 125% |
| 2 - Alta | 5389–6168 | 100% |
| 2 - Alta | 6169–6252 | 75% |
| 2 - Alta | 6253–6336 | 50% |
| 2 - Alta | > 6336 | 0% |
| 3 - Média | < 19489 | 150% |
| 3 - Média | 19489–22116 | 125% |
| 3 - Média | 22117–22524 | 100% |
| 3 - Média | 22525–23892 | 75% |
| 3 - Média | 23893–24276 | 50% |
| 3 - Média | > 24276 | 0% |

Versão: 2
