# Quizclayverson

Crie uma landing page de UMA ÚNICA TELA (SPA em React + Tailwind) em formato de QUIZ DE QUALIFICAÇÃO para a marca pessoal de Clayverson Demontier, gestor de tráfego pago e profissional de vendas. A pessoa chega de um anúncio de captação, responde 6 perguntas rápidas, deixa nome e WhatsApp, vê um diagnóstico e vai para o WhatsApp com o resumo das respostas já preenchido. Idioma: português do Brasil, linguagem simples, de 6ª série, para qualquer pessoa leiga. PROIBIDO jargão (nada de CPL, ROAS, funil, criativo, CPM, pixel).

REGRAS GERAIS
- Mobile-first (360px), uma pergunta por tela, sem menu, sem links que tirem a pessoa da página (exceto WhatsApp e o material gratuito).
- Proibido prometer resultado ("vou te fazer faturar", "retorno garantido"). Rodapé: "Diagnóstico inicial e gratuito. Não garante resultados."
- Credenciais em 3 chips: "6 anos em tráfego pago", "+R$ 5 milhões gerenciados em anúncios", "+R$ 10 milhões em faturamento gerado para clientes". [PLACEHOLDER: confirmar a moeda e ter comprovação (prints/relatórios) antes de publicar]. Não inventar depoimentos nem números.
- Constantes no topo do código, fáceis de editar: WHATSAPP_NUMBER = [55DDDNÚMERO], PIXEL_ID = [PIXEL_ID], LINK_MATERIAL_GRATUITO = [URL], FOTO_CLAYVERSON = [caminho da foto no repositório]. Utilize a foto anexada do estrategista Clayverson Demontier salva na pasta de assets/public do projeto.

DESIGN SYSTEM (leigo entende de relance)
- Cores: fundo #F8FAFC; texto #0F172A; azul-marinho #0B1F3A (capa e rodapé); azul principal #2563EB; verde de ação #16A34A (hover #15803D, texto branco); amarelo de destaque #F59E0B; vermelho de alerta #DC2626 (só em alertas); borda #E2E8F0. Contraste mínimo 4.5:1 (7:1 em textos pequenos).
- Fonte única: Inter (400, 600, 800), display=swap. Títulos 28-34px peso 800; corpo e opções 18px; nada abaixo de 16px.
- Opções: cartões grandes (altura 64-72px, cantos 16px), ícone lucide à esquerda (28px) e texto 18px peso 600. Ao tocar: borda azul 2px, fundo azul-claro, ícone de check e leve escala. Avanço automático 300ms. Botões com 56px de altura, largura total.
- Animações leves (fade/slide 250ms), respeitando prefers-reduced-motion. Foco visível e áreas de toque grandes.

FUNIL VISUAL (fixo no topo, durante as perguntas)
- Funil em SVG com 6 faixas que se estreitam; cada pergunta respondida preenche a faixa (as primeiras em azul, as últimas em verde). Ao lado: "Etapa 3 de 6 · Faturamento" e barra de progresso em %. Nomes das etapas: Negócio · Desafio · Faturamento · Investimento · Atendimento · Prazo. A tela de contato acende uma 7ª faixa "Diagnóstico".

TELAS (copy exata)

0) CAPA (fundo azul-marinho)
- Selo: "DIAGNÓSTICO GRATUITO · 1 MINUTO"
- H1: "Seu negócio está pronto para ter mais clientes com anúncios?"
- Sub: "Responda 6 perguntas rápidas. Eu analiso o seu cenário e te chamo no WhatsApp com um direcionamento para o seu caso."
- Foto do Clayverson (usar a foto anexada), os 3 chips de credencial e o botão verde "COMEÇAR O DIAGNÓSTICO →". Microcopy: "Leva cerca de 1 minuto · Sem compromisso".

1) "Qual é o segmento do seu negócio?" (ajuda: "Escolha a mais parecida.")
Opções: Clínica, saúde ou estética · Advocacia ou serviços profissionais · Loja ou e-commerce · Imobiliária ou construção · Infoprodutos, cursos ou mentoria · Prestador de serviço local · Outro.

2) "O que mais trava o seu resultado hoje?"
Opções: Poucos clientes chegando · Chega gente, mas poucos compram · Pago caro por cada contato · Não sei o que está funcionando · Quero crescer, mas com segurança.

3) "Quanto o seu negócio fatura por mês, mais ou menos?" (ajuda: "Pode ser aproximado. Isso me ajuda a indicar o melhor caminho.")
Opções: Ainda não fatura (0) · Até R$ 10 mil (1) · R$ 10 a 30 mil (2) · R$ 30 a 100 mil (3) · R$ 100 a 300 mil (4) · Acima de R$ 300 mil (5).

TELA INTERMEDIÁRIA (depois da pergunta 3): "Metade do caminho!" com o texto "Suas respostas me ajudam a montar um direcionamento só seu, e não um discurso pronto." e os 3 chips de credencial. [PLACEHOLDER: espaço para um print de resultado real, com autorização do cliente].

4) "Quanto você pode investir por mês em anúncios?" (ajuda: "Só o valor pago às plataformas de anúncio, sem contar o meu serviço.")
Opções: Menos de R$ 1.000 (0) · R$ 1.000 a 3.000 (2) · R$ 3.000 a 10.000 (3) · R$ 10.000 a 30.000 (4) · Acima de R$ 30.000 (5) · Ainda não sei (1).

5) "Quem atende os contatos que chegam?"
Opções: Eu mesmo, pelo WhatsApp (1) · Uma atendente ou recepção (2) · Uma equipe de vendas (3) · Ainda não tenho ninguém (0).

6) "Quando você quer começar?"
Opções: O quanto antes (esta semana) (3) · Nos próximos 30 dias (2) · Só estou pesquisando (0).

7) CONTATO: "Quase lá! Para onde envio o seu direcionamento?"
Campos: "Seu nome" e "Seu WhatsApp (com DDD)" com máscara e validação (10 ou 11 dígitos). Checkbox obrigatório e desmarcado: "Concordo em ser contatado pelo WhatsApp e com a Política de Privacidade" (link abre modal [PLACEHOLDER: texto com identificação do responsável, finalidade, prazo de guarda e contato]). Botão verde "VER MEU DIAGNÓSTICO →".

8) ANÁLISE (2,5 s): "Analisando suas respostas…" com 3 itens que vão sendo marcados: "Entendendo seu segmento ✓", "Avaliando seu momento ✓", "Montando seu direcionamento ✓".

PONTUAÇÃO E NÍVEL
Pontos de cada resposta como indicado nas opções (faturamento 0-5, investimento 0-5, atendimento 0-3, prazo 0-3; máximo 16).
- FRIO: pontuação ≤ 5 OU investimento = "Menos de R$ 1.000".
- QUENTE: pontuação ≥ 11 e não FRIO.
- MORNO: todos os demais.
(Limites em constantes editáveis.)

RESULTADO (mostrar um medidor semicircular em cores: vermelho/amarelo/verde)
- QUENTE: "{nome}, seu momento: PRONTO PARA ACELERAR". Texto: "Pelas suas respostas, você já tem base, verba e urgência. O próximo passo é conversarmos para montar o plano." Botão: "FALAR COM O CLAYVERSON NO WHATSAPP". Abaixo: "Seu resumo vai junto na mensagem. Você não precisa repetir nada."
- MORNO: "{nome}, seu momento: PRONTO PARA COMEÇAR COM ESTRUTURA". Texto: "Você tem potencial, mas alguns pontos precisam ser ajustados antes de investir mais. Vamos conversar para eu te mostrar quais." Mesmo botão.
- FRIO: "{nome}, seu momento: ANTES DE ANUNCIAR, ORGANIZE A BASE". Texto: "Pelo que você respondeu, anunciar agora pode gastar seu dinheiro sem o retorno esperado. Prefiro ser direto com você." Botão principal: "BAIXAR O MATERIAL GRATUITO" (LINK_MATERIAL_GRATUITO). Botão secundário discreto: "Mesmo assim, quero falar com o Clayverson" (WhatsApp).
Em todos, mostrar "O que eu vi nas suas respostas" com até 3 itens (regras):
- Pergunta 2 "Poucos clientes chegando" → "Seu foco inicial: gerar mais contatos com o público certo."
- "Chega gente, mas poucos compram" → "Seu foco: qualificar quem chega e melhorar o atendimento comercial."
- "Pago caro por cada contato" → "Seu foco: reduzir o custo de cada contato."
- "Não sei o que está funcionando" → "Seu foco: medir direito, para decidir com dados."
- "Quero crescer, mas com segurança" → "Seu foco: escalar com controle de custo e processo."
- Atendimento = "Ainda não tenho ninguém" → "Alerta: sem alguém para responder rápido, os contatos esfriam."
- Investimento = "Menos de R$ 1.000" → "Atenção: com verba muito baixa, o aprendizado é lento."

WHATSAPP
Link: https://wa.me/{WHATSAPP_NUMBER}?text={mensagem codificada}. Mensagem:
"Olá, Clayverson! Fiz o diagnóstico no seu site.
Nome: {nome}
Segmento: {segmento}
Maior desafio: {desafio}
Faturamento mensal: {faturamento}
Investimento em anúncios: {investimento}
Quem atende os contatos: {atendimento}
Quando quer começar: {prazo}
Resultado: {pronto para acelerar | pronto para começar com estrutura | antes de anunciar, organizar a base}
Código: {Q-ALTA | M-MEDIA | F-INICIAL}"
Disparar o evento de Lead ao concluir o contato e o de Contact ao clicar no WhatsApp (redirecionar após ~200 ms).

DADOS (Lovable Cloud)
Tabela "leads": id, criado_em, nome, whatsapp, segmento, desafio, faturamento, investimento, atendimento, prazo, pontuacao, nivel, utm_source, utm_medium, utm_campaign, utm_content, utm_term, fbclid, consentimento (boolean), texto_consentimento_versao. Gravar SOMENTE após o aceite. Política: inserção permitida ao visitante; leitura e exclusão só pelo dono (Clayverson). Capturar UTMs e fbclid da URL na entrada.

TRACKING (Meta Pixel PIXEL_ID, sem dados pessoais)
PageView; trackCustom Quiz_Start (no botão da capa) e Quiz_Step com {etapa}; Lead ao concluir o contato, com {nivel}; trackCustom Quiz_Quente, Quiz_Morno ou Quiz_Frio; Contact ao clicar no WhatsApp.

ESTADO E UX
Respostas em estado e sessionStorage; botão voltar do navegador volta a etapa anterior (history.pushState); seta de voltar na tela. Sem rolagem durante as perguntas.

DESEMPENHO E ACESSIBILIDADE
Sem bibliotecas pesadas; imagens em WebP; aria-labels e navegação por teclado; carregamento rápido no 4G.

QA FINAL
Testar em iPhone (Safari) e Android (Chrome): avanço, voltar, máscara do telefone, gravação no banco, mensagem do WhatsApp preenchida e acentos codificados, eventos do pixel disparando uma vez cada.

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://quizclayverson.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/aab3c4b0-62dd-449e-8547-61bfbf79ee1e).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
