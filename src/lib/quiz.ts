// ====== CONSTANTES EDITÁVEIS ======
export const WHATSAPP_NUMBER = "5585996288719";
export const PIXEL_ID = "1418598996441763";
export const LINK_MATERIAL_GRATUITO = "[URL]";
export const FOTO_CLAYVERSON = "/clayverson.webp";
export const TEXTO_CONSENTIMENTO_VERSAO = "v1-2026-10-24";

// Limites de nível
export const LIMITE_FRIO_MAX = 5; // pontuação <= 5 => FRIO
export const LIMITE_QUENTE_MIN = 11; // pontuação >= 11 => QUENTE
export const INVESTIMENTO_FRIO = "Menos de R$ 1.000";

export type Nivel = "QUENTE" | "MORNO" | "FRIO";
export type Opcao = { label: string; pontos?: number; icon: string };
export type Pergunta = {
  id: "segmento" | "desafio" | "faturamento" | "investimento" | "atendimento" | "prazo";
  etapa: string;
  titulo: string;
  ajuda?: string;
  opcoes: Opcao[];
};

export const PERGUNTAS: Pergunta[] = [
  {
    id: "segmento",
    etapa: "Negócio",
    titulo: "Qual é o segmento do seu negócio?",
    ajuda: "Escolha a mais parecida.",
    opcoes: [
      { label: "Clínica, saúde ou estética", icon: "Stethoscope" },
      { label: "Advocacia ou serviços profissionais", icon: "Scale" },
      { label: "Loja ou e-commerce", icon: "ShoppingBag" },
      { label: "Imobiliária ou construção", icon: "Building2" },
      { label: "Infoprodutos, cursos ou mentoria", icon: "GraduationCap" },
      { label: "Prestador de serviço local", icon: "Wrench" },
      { label: "Outro", icon: "MoreHorizontal" },
    ],
  },
  {
    id: "desafio",
    etapa: "Desafio",
    titulo: "O que mais trava o seu resultado hoje?",
    opcoes: [
      { label: "Poucos clientes chegando", icon: "UserMinus" },
      { label: "Chega gente, mas poucos compram", icon: "Users" },
      { label: "Pago caro por cada contato", icon: "BadgeDollarSign" },
      { label: "Não sei o que está funcionando", icon: "HelpCircle" },
      { label: "Quero crescer, mas com segurança", icon: "ShieldCheck" },
    ],
  },
  {
    id: "faturamento",
    etapa: "Faturamento",
    titulo: "Quanto o seu negócio fatura por mês, mais ou menos?",
    ajuda: "Pode ser aproximado. Isso me ajuda a indicar o melhor caminho.",
    opcoes: [
      { label: "Ainda não fatura", pontos: 0, icon: "CircleOff" },
      { label: "Até R$ 10 mil", pontos: 1, icon: "Coins" },
      { label: "R$ 10 a 30 mil", pontos: 2, icon: "Wallet" },
      { label: "R$ 30 a 100 mil", pontos: 3, icon: "Banknote" },
      { label: "R$ 100 a 300 mil", pontos: 4, icon: "TrendingUp" },
      { label: "Acima de R$ 300 mil", pontos: 5, icon: "Rocket" },
    ],
  },
  {
    id: "investimento",
    etapa: "Investimento",
    titulo: "Quanto você pode investir por mês em anúncios?",
    ajuda: "Só o valor pago às plataformas de anúncio, sem contar o meu serviço.",
    opcoes: [
      { label: "Menos de R$ 1.000", pontos: 0, icon: "Coins" },
      { label: "R$ 1.000 a 3.000", pontos: 2, icon: "Wallet" },
      { label: "R$ 3.000 a 10.000", pontos: 3, icon: "Banknote" },
      { label: "R$ 10.000 a 30.000", pontos: 4, icon: "TrendingUp" },
      { label: "Acima de R$ 30.000", pontos: 5, icon: "Rocket" },
      { label: "Ainda não sei", pontos: 1, icon: "HelpCircle" },
    ],
  },
  {
    id: "atendimento",
    etapa: "Atendimento",
    titulo: "Quem atende os contatos que chegam?",
    opcoes: [
      { label: "Eu mesmo, pelo WhatsApp", pontos: 1, icon: "Smartphone" },
      { label: "Uma atendente ou recepção", pontos: 2, icon: "Headset" },
      { label: "Uma equipe de vendas", pontos: 3, icon: "Users" },
      { label: "Ainda não tenho ninguém", pontos: 0, icon: "UserX" },
    ],
  },
  {
    id: "prazo",
    etapa: "Prazo",
    titulo: "Quando você quer começar?",
    opcoes: [
      { label: "O quanto antes (esta semana)", pontos: 3, icon: "Zap" },
      { label: "Nos próximos 30 dias", pontos: 2, icon: "CalendarDays" },
      { label: "Só estou pesquisando", pontos: 0, icon: "Search" },
    ],
  },
];

export type Respostas = Partial<Record<Pergunta["id"], string>>;

export function pontuar(r: Respostas): number {
  let total = 0;
  for (const p of PERGUNTAS) {
    const o = p.opcoes.find((x) => x.label === r[p.id]);
    total += o?.pontos ?? 0;
  }
  return total;
}

export function nivelDe(r: Respostas): Nivel {
  const s = pontuar(r);
  if (s <= LIMITE_FRIO_MAX || r.investimento === INVESTIMENTO_FRIO) return "FRIO";
  if (s >= LIMITE_QUENTE_MIN) return "QUENTE";
  return "MORNO";
}

export const NIVEL_INFO: Record<Nivel, { titulo: string; texto: string; resumo: string; codigo: string }> = {
  QUENTE: {
    titulo: "PRONTO PARA ACELERAR",
    texto: "Pelas suas respostas, você já tem base, verba e urgência. O próximo passo é conversarmos para montar o plano.",
    resumo: "pronto para acelerar",
    codigo: "Q-ALTA",
  },
  MORNO: {
    titulo: "PRONTO PARA COMEÇAR COM ESTRUTURA",
    texto: "Você tem potencial, mas alguns pontos precisam ser ajustados antes de investir mais. Vamos conversar para eu te mostrar quais.",
    resumo: "pronto para começar com estrutura",
    codigo: "M-MEDIA",
  },
  FRIO: {
    titulo: "ANTES DE ANUNCIAR, ORGANIZE A BASE",
    texto: "Pelo que você respondeu, anunciar agora pode gastar seu dinheiro sem o retorno esperado. Prefiro ser direto com você.",
    resumo: "antes de anunciar, organizar a base",
    codigo: "F-INICIAL",
  },
};

const FOCOS: Partial<Record<string, string>> = {
  "Poucos clientes chegando": "Seu foco inicial: gerar mais contatos com o público certo.",
  "Chega gente, mas poucos compram": "Seu foco: qualificar quem chega e melhorar o atendimento comercial.",
  "Pago caro por cada contato": "Seu foco: reduzir o custo de cada contato.",
  "Não sei o que está funcionando": "Seu foco: medir direito, para decidir com dados.",
  "Quero crescer, mas com segurança": "Seu foco: escalar com controle de custo e processo.",
};

export type Insight = { texto: string; tipo: "foco" | "alerta" };
export function insights(r: Respostas): Insight[] {
  const out: Insight[] = [];
  const foco = r.desafio ? FOCOS[r.desafio] : undefined;
  if (foco) out.push({ texto: foco, tipo: "foco" });
  if (r.atendimento === "Ainda não tenho ninguém")
    out.push({ texto: "Alerta: sem alguém para responder rápido, os contatos esfriam.", tipo: "alerta" });
  if (r.investimento === INVESTIMENTO_FRIO)
    out.push({ texto: "Atenção: com verba muito baixa, o aprendizado é lento.", tipo: "alerta" });
  return out.slice(0, 3);
}

export function mensagemWhatsApp(nome: string, r: Respostas, nivel: Nivel, telefone = ""): string {
  const i = NIVEL_INFO[nivel];
  return [
    "Olá, Clayverson! Concluí o diagnóstico e quero agendar minha consultoria gratuita para o meu negócio.",
    "Quero analisar minha estrutura atual, meus anúncios e o que posso melhorar.",
    "",
    "📋 RESUMO DO MEU DIAGNÓSTICO",
    `Nome: ${nome}`,
    `WhatsApp informado: ${telefone}`,
    `Segmento: ${r.segmento ?? ""}`,
    `Maior desafio: ${r.desafio ?? ""}`,
    `Faturamento mensal: ${r.faturamento ?? ""}`,
    `Investimento em anúncios: ${r.investimento ?? ""}`,
    `Quem atende os contatos: ${r.atendimento ?? ""}`,
    `Quando quer começar: ${r.prazo ?? ""}`,
    `Resultado: ${i.resumo}`,
    `Código: ${i.codigo}`,
  ].join("\n");
}

export function linkWhatsApp(texto: string): string {
  return `https://wa.me/${WHATSAPP_NUMBER.replace(/\D/g, "")}?text=${encodeURIComponent(texto)}`;
}

export function mascaraTelefone(v: string): string {
  const d = v.replace(/\D/g, "").slice(0, 11);
  if (d.length <= 2) return d.length ? `(${d}` : "";
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`;
  if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
}

export function telefoneValido(v: string): boolean {
  const n = v.replace(/\D/g, "").length;
  return n === 10 || n === 11;
}
