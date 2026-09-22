# Roteiro do Vídeo Pitch — AIOps Forecaster (Grupo 18)
### Sprint 4 — Enterprise Challenge Locaweb | 2TSCOA
Duração alvo: **até 5 minutos** | Formato: hands-on, seguindo o PPT final

> Como usar este roteiro: cada bloco indica quem fala (sugestão — ajustem livremente entre os 3 integrantes), o tempo alvo, o que dizer e qual slide/tela mostrar. Treinem em voz alta cronometrando antes de gravar a versão final. Falem com naturalidade — usem este texto como guia, não para decorar palavra por palavra.

---

## 1. Abertura e contextualização do desafio (~30s)
**Quem fala:** Integrante 1
**Tela:** Slide 1 (título) → Slide 2 (contextualização)

> "Olá! Somos o Grupo 18, e vamos apresentar o **AIOps Forecaster** — nossa solução para o Enterprise Challenge da Locaweb.
> A Locaweb opera uma infraestrutura de tecnologia crítica, 24 horas por dia, 7 dias por semana. Só na nossa base histórica, analisamos mais de **122 mil incidentes** registrados entre 2023 e 2025. Hoje, as equipes agem de forma **reativa**: só respondem depois que a falha já aconteceu — o que coloca em risco o cumprimento dos OLAs, os Acordos de Nível Operacional."

---

## 2. Objetivo do projeto (~30s)
**Quem fala:** Integrante 1 ou 2
**Tela:** Slide 3 (objetivo)

> "Nosso objetivo é transformar esse cenário reativo em um cenário **preditivo**. Isso significa: antecipar o volume de incidentes para o dia seguinte (D+1) e para a semana seguinte (D+7), identificar tendências de risco de perda de OLA, e apoiar a decisão operacional indicando exatamente onde agir — por equipe, produto ou ativo crítico."

---

## 3. Proposta de solução (~1 min)
**Quem fala:** Integrante 2
**Tela:** Slide 4 (proposta) → Slide 5 (arquitetura)

> "Projetamos a solução para rodar em um ecossistema gerenciado no **Google Cloud Platform** — BigQuery como Data Warehouse e Vertex AI para o treinamento dos modelos. Essa é a nossa arquitetura de referência para produção.
> Como o ambiente acadêmico não nos dá acesso pago a essa infraestrutura, implementamos o MVP de forma simplificada: um pipeline em **Python**, com engenharia de features temporais — lags, médias móveis, variáveis de calendário — e os modelos de fato treinados localmente com **XGBoost** e **Random Forest**, sobre os mesmos dados e a mesma lógica.
> Os resultados alimentam dashboards no **Looker Studio**, transformando previsão em alerta acionável para as equipes de operação — e essa parte já está funcionando de verdade, não é só conceito."

---

## 4. Demonstração da solução funcionando (~2 min) — **o coração do vídeo**
**Quem fala:** Integrante 3 (compartilhando tela)
**Tela:** Navegação real no Looker Studio / aplicação — **não usar apenas prints estáticos**

> "Agora vamos mostrar a solução funcionando na prática."

Roteiro sugerido de navegação (ajustem à tela real de vocês):
1. Abrir o painel de **previsão D+1** — mostrar o volume projetado de incidentes e destacar o filtro por prioridade P2/P3.
2. Passar para o painel de **tendência D+7** — mostrar a comparação entre histórico e projeção.
3. Mostrar o **classificador de risco de OLA** — a probabilidade de violação por produto/equipe, e comentar o resultado de ROC-AUC de 87,3%.
4. Abrir a **matriz de recomendações / alertas** — mostrar uma recomendação prática real (ex.: "ajustar equipe Team11" ou "abrir Problem Record para o ativo IC00840").
5. Aplicar 1 ou 2 filtros ao vivo (por severidade, por grupo de atendimento) para provar que o painel é interativo.

> "Como vocês podem ver, o dashboard não é só um relatório — ele indica, com antecedência, onde a operação deve agir para evitar o próximo incidente crítico."

**Dica:** gravem esta parte com tela cheia do dashboard, sem cortes bruscos, e sincronizem a fala com o que está sendo clicado.

---

## 5. Benefícios gerados (~30s)
**Quem fala:** Integrante 1
**Tela:** Slide 10 (benefícios)

> "Os benefícios vão além da tecnologia. Passamos de uma cultura reativa para uma cultura orientada a dados; melhoramos a disponibilidade dos serviços entregues aos clientes da Locaweb; reduzimos o estresse das equipes técnicas diante de picos inesperados; e, principalmente, ganhamos tempo para agir antes que o OLA seja violado."

---

## 6. Conclusão e próximos passos (~30s)
**Quem fala:** Integrante 2 ou 3
**Tela:** Slide 11 (conclusão) → Slide 12 (links/encerramento)

> "Ao longo das quatro sprints, evoluímos de uma ideia para um MVP funcional com modelos validados e explicáveis. Como próximos passos, queremos automatizar totalmente os pipelines no Cloud Composer, ampliar a cobertura para outras prioridades e produtos, e manter os modelos em retreinamento contínuo.
> O **AIOps Forecaster** mostra que é possível transformar 122 mil incidentes em decisões antecipadas — e não apenas em relatórios do que já aconteceu.
> Muito obrigado! Somos o Grupo 18, e essa foi a nossa solução para a Locaweb."

---

## Checklist antes de gravar
- [ ] Cronometrar um ensaio completo (meta: ficar entre 4:30 e 5:00)
- [ ] Confirmar que o dashboard/aplicação está com dados carregados e sem erros na tela
- [ ] Testar áudio e iluminação de quem estiver na câmera
- [ ] Gravar a demonstração de tela (item 4) separadamente, se for mais fácil, e editar depois
- [ ] Subir o vídeo final no YouTube (não listado ou público — nunca "privado", pois a banca precisa acessar)
- [ ] Colar o link do YouTube no slide de encerramento do PPT antes da entrega final
