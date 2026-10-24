import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState, type ComponentType } from "react";
import {
  ArrowLeft, ArrowRight, Check, Stethoscope, Scale, ShoppingBag, Building2, GraduationCap, Wrench,
  MoreHorizontal, UserMinus, Users, BadgeDollarSign, HelpCircle, ShieldCheck, CircleOff, Coins, Wallet,
  Banknote, TrendingUp, Rocket, Smartphone, Headset, UserX, Zap, CalendarDays, Search, AlertTriangle,
  Target, MessageCircle, X, Loader2,
} from "lucide-react";
import { QuizVideo } from "@/components/quiz-video";
import { QUIZ_VIDEOS } from "@/lib/media";
import { supabase } from "@/integrations/supabase/client";
import {
  PERGUNTAS, PIXEL_ID, FOTO_CLAYVERSON, WHATSAPP_NUMBER, TEXTO_CONSENTIMENTO_VERSAO, NIVEL_INFO,
  nivelDe, pontuar, insights, mensagemWhatsApp, linkWhatsApp, mascaraTelefone, telefoneValido,
  type Respostas, type Nivel,
} from "@/lib/quiz";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Diagnóstico gratuito de anúncios · Clayverson Demontier" },
      { name: "description", content: "Responda 6 perguntas rápidas e receba no WhatsApp um direcionamento para o seu negócio ter mais clientes com anúncios." },
      { property: "og:title", content: "Seu negócio está pronto para ter mais clientes com anúncios?" },
      { property: "og:description", content: "Diagnóstico gratuito em 1 minuto com Clayverson Demontier." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

const ICONS: Record<string, ComponentType<{ size?: number; className?: string; "aria-hidden"?: boolean }>> = {
  Stethoscope, Scale, ShoppingBag, Building2, GraduationCap, Wrench, MoreHorizontal, UserMinus, Users,
  BadgeDollarSign, HelpCircle, ShieldCheck, CircleOff, Coins, Wallet, Banknote, TrendingUp, Rocket,
  Smartphone, Headset, UserX, Zap, CalendarDays, Search,
};

type Step = "capa" | "q0" | "q1" | "q2" | "meio" | "q3" | "q4" | "q5" | "contato" | "analise" | "resultado";
const STORE = "quiz-clayverson";
const UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "fbclid"] as const;

// ---------- Pixel ----------
declare global {
  interface Window {
    fbq?: ((...args: unknown[]) => void) & { callMethod?: (...a: unknown[]) => void; queue?: unknown[]; loaded?: boolean; version?: string; push?: unknown };
    _fbq?: unknown;
  }
}
const pixelAtivo = () => !PIXEL_ID.startsWith("[");
const disparados = new Set<string>();
function track(kind: "track" | "trackCustom", name: string, params?: Record<string, unknown>, onceKey = name) {
  if (typeof window === "undefined" || !pixelAtivo() || !window.fbq) return;
  if (disparados.has(onceKey)) return;
  disparados.add(onceKey);
  const eventId = crypto.randomUUID();
  window.fbq(kind, name, params ?? {}, { eventID: eventId });
  void fetch("/api/meta-events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    keepalive: true,
    body: JSON.stringify({ name, eventId, sourceUrl: location.href, params: params ?? {} }),
  }).catch(() => { /* A medição nunca bloqueia o quiz. */ });
}
function carregarPixel() {
  if (!pixelAtivo() || window.fbq) return;
  /* eslint-disable */
  const n: any = function (...args: unknown[]) { n.callMethod ? n.callMethod.apply(n, args) : n.queue.push(args); };
  n.push = n; n.loaded = true; n.version = "2.0"; n.queue = [];
  window.fbq = n; window._fbq = n;
  const s = document.createElement("script"); s.async = true; s.src = "https://connect.facebook.net/en_US/fbevents.js";
  document.head.appendChild(s);
  n("init", PIXEL_ID, {}, { agent: "lovable" });
  track("track", "PageView");
}

// ---------- Página ----------
function Index() {
  const [step, setStep] = useState<Step>("capa");
  const [respostas, setRespostas] = useState<Respostas>({});
  const [nome, setNome] = useState("");
  const [tel, setTel] = useState("");
  const [pronto, setPronto] = useState(false);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(STORE);
      if (raw) {
        const d = JSON.parse(raw);
        setRespostas(d.respostas ?? {}); setNome(d.nome ?? ""); setTel(d.tel ?? "");
        const s: Step = d.step === "analise" ? "resultado" : d.step ?? "capa";
        setStep(s); history.replaceState({ step: s }, "");
      } else history.replaceState({ step: "capa" }, "");
      const q = new URLSearchParams(location.search);
      if (!sessionStorage.getItem(STORE + "-utm")) {
        const u: Record<string, string> = {};
        UTM_KEYS.forEach((k) => { const v = q.get(k); if (v) u[k] = v.slice(0, 300); });
        sessionStorage.setItem(STORE + "-utm", JSON.stringify(u));
      }
    } catch { /* ignore */ }
    carregarPixel();
    const onPop = (e: PopStateEvent) => {
      const s = (e.state?.step as Step) ?? "capa";
      if (s === "analise") { history.back(); return; }
      setStep(s);
    };
    window.addEventListener("popstate", onPop);
    setPronto(true);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  useEffect(() => {
    if (!pronto) return;
    sessionStorage.setItem(STORE, JSON.stringify({ step, respostas, nome, tel }));
  }, [step, respostas, nome, tel, pronto]);

  const go = (s: Step) => {
    history.pushState({ step: s }, "");
    setStep(s);
    window.scrollTo(0, 0);
  };
  const voltar = () => history.back();

  const nivel = nivelDe(respostas);

  if (step === "capa") return <Capa onStart={() => { track("trackCustom", "Quiz_Start"); go("q0"); }} />;
  if (step === "meio") return <Meio onNext={() => go("q3")} onBack={voltar} />;
  if (step === "contato")
    return (
      <Contato nome={nome} setNome={setNome} tel={tel} setTel={setTel} onBack={voltar}
        respostas={respostas}
        onDone={(n) => {
          track("trackCustom", n === "QUENTE" ? "Quiz_Quente" : n === "MORNO" ? "Quiz_Morno" : "Quiz_Frio");
          go("analise");
        }} />
    );
  if (step === "analise") return <Analise onDone={() => { history.replaceState({ step: "resultado" }, ""); setStep("resultado"); }} />;
  if (step === "resultado") return <Resultado nome={nome} telefone={tel} respostas={respostas} nivel={nivel} />;

  const idx = Number(step.slice(1));
  const p = PERGUNTAS[idx]!;
  return (
    <Pergunta
      idx={idx}
      key={p.id}
      selecionada={respostas[p.id]}
      onBack={voltar}
      onPick={(label) => {
        setRespostas((r) => ({ ...r, [p.id]: label }));
        track("trackCustom", "Quiz_Step", { etapa: p.etapa }, "step-" + p.id);
        if (idx === PERGUNTAS.length - 1) {
          track("track", "InitiateCheckout", { etapa: p.etapa });
        }
        setTimeout(() => go(idx === 2 ? "meio" : idx === 5 ? "contato" : (`q${idx + 1}` as Step)), 300);
      }}
    />
  );
}

// ---------- Componentes ----------
function Chips({ dark }: { dark?: boolean }) {
  const itens = ["6 anos em tráfego pago", "+R$ 5 milhões gerenciados em anúncios", "+R$ 10 milhões em faturamento gerado para clientes"];
  return (
    <ul className="flex flex-wrap justify-center gap-2" aria-label="Credenciais">
      {itens.map((t) => (
        <li key={t} className={`rounded-full px-3 py-1.5 text-base font-semibold ${dark ? "bg-navy-foreground/10 text-navy-foreground border border-navy-foreground/20" : "bg-card text-foreground border border-border"}`}>
          <span className="text-warning" aria-hidden>★ </span>{t}
        </li>
      ))}
    </ul>
  );
}

function Rodape({ dark }: { dark?: boolean }) {
  return <p className={`py-4 text-center text-base ${dark ? "text-navy-foreground/80" : "text-muted-foreground"}`}>Diagnóstico inicial e gratuito. Não garante resultados.</p>;
}

function BotaoVerde({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button {...props} className="flex min-h-14 w-full items-center justify-center gap-2 rounded-2xl bg-success px-4 py-3 text-lg font-extrabold text-success-foreground shadow-lg transition-colors hover:bg-success-hover focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-warning disabled:opacity-60">
      {children}
    </button>
  );
}

function Capa({ onStart }: { onStart: () => void }) {
  return (
    <main className="min-h-[100dvh] bg-navy text-navy-foreground">
      <div className="mx-auto flex min-h-[100dvh] max-w-md flex-col items-center px-5 pt-8 text-center anim-in">
        <span className="rounded-full bg-warning px-3 py-1.5 text-base whitespace-nowrap font-extrabold text-foreground">DIAGNÓSTICO GRATUITO · 1 MINUTO</span>
        <h1 className="mt-5 text-[30px] font-extrabold leading-tight">Seu negócio está pronto para ter mais clientes com anúncios?</h1>
        <p className="mt-3 text-lg text-navy-foreground/90">Responda 6 perguntas rápidas. Eu analiso o seu cenário e te chamo no WhatsApp com um direcionamento para o seu caso.</p>
        <img src={FOTO_CLAYVERSON} alt="Clayverson Demontier, gestor de tráfego pago" width={160} height={160}
          className="mt-6 h-40 w-40 rounded-full border-4 border-warning object-cover object-top" />
        <p className="mt-2 text-lg font-semibold">Clayverson Demontier</p>
        <div className="mt-4"><Chips dark /></div>
        <div className="mt-6 w-full"><BotaoVerde onClick={onStart}>COMEÇAR O DIAGNÓSTICO <ArrowRight aria-hidden /></BotaoVerde></div>
        <p className="mt-3 text-base text-navy-foreground/80">Leva cerca de 1 minuto · Sem compromisso</p>
        <div className="mt-auto"><Rodape dark /></div>
      </div>
    </main>
  );
}

const ETAPAS = [...PERGUNTAS.map((p) => p.etapa), "Diagnóstico"];
function Funil({ preenchidas, atual }: { preenchidas: number; atual: number }) {
  const pct = Math.round((Math.min(preenchidas, 6) / 6) * 100);
  return (
    <div className="flex items-center gap-3">
      <svg viewBox="0 0 80 70" width="64" height="56" aria-hidden>
        {ETAPAS.map((_, i) => {
          const top = 4 + i * 9.4, w1 = 76 - i * 8, w2 = 76 - (i + 1) * 8;
          const on = i < preenchidas;
          const fill = on ? (i < 3 ? "var(--primary)" : "var(--success)") : "var(--border)";
          return <polygon key={i} points={`${40 - w1 / 2},${top} ${40 + w1 / 2},${top} ${40 + w2 / 2},${top + 8.4} ${40 - w2 / 2},${top + 8.4}`} fill={fill} />;
        })}
      </svg>
      <div className="flex-1">
        <p className="text-base font-semibold">{atual <= 6 ? `Etapa ${atual} de 6 · ${ETAPAS[atual - 1]}` : "Etapa final · Diagnóstico"}</p>
        <div className="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-border" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label="Progresso">
          <div className="h-full rounded-full bg-primary transition-all duration-300" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <span className="text-base font-extrabold text-primary">{pct}%</span>
    </div>
  );
}

function Topo({ onBack, preenchidas, atual }: { onBack: () => void; preenchidas: number; atual: number }) {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background/95 px-4 py-3 backdrop-blur">
      <div className="mx-auto flex max-w-md items-center gap-2">
        <button onClick={onBack} aria-label="Voltar" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring">
          <ArrowLeft size={24} aria-hidden />
        </button>
        <div className="flex-1"><Funil preenchidas={preenchidas} atual={atual} /></div>
      </div>
    </header>
  );
}

function Pergunta({ idx, selecionada, onPick, onBack }: { idx: number; selecionada?: string | undefined; onPick: (l: string) => void; onBack: () => void }) {
  const p = PERGUNTAS[idx]!;
  const [pick, setPick] = useState<string | undefined>(undefined);
  return (
    <main className="flex h-[100dvh] flex-col overflow-hidden">
      <Topo onBack={onBack} preenchidas={idx} atual={idx + 1} />
      <section className="mx-auto flex w-full max-w-md flex-1 flex-col overflow-y-auto px-4 pb-4 pt-4 anim-in">
        <h1 className="text-[28px] font-extrabold leading-tight">{p.titulo}</h1>
        {p.ajuda && <p className="mt-1 text-base text-muted-foreground">{p.ajuda}</p>}
        <div role="radiogroup" aria-label={p.titulo} className="mt-4 flex flex-col gap-2.5">
          {p.opcoes.map((o) => {
            const Icon = ICONS[o.icon] ?? HelpCircle;
            const on = (pick ?? selecionada) === o.label;
            return (
              <button key={o.label} role="radio" aria-checked={on} disabled={!!pick}
                onClick={() => { setPick(o.label); onPick(o.label); }}
                className={`flex min-h-16 w-full items-center gap-3 rounded-2xl border-2 px-4 py-3 text-left text-lg font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-ring/40 ${on ? "scale-[1.02] border-primary bg-primary-soft" : "border-border bg-card hover:border-primary/50"}`}>
                <Icon size={28} className="shrink-0 text-primary" aria-hidden />
                <span className="flex-1">{o.label}</span>
                {on && <Check size={24} className="text-primary" aria-hidden />}
              </button>
            );
          })}
        </div>
      </section>
    </main>
  );
}

function Meio({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  return (
    <main className="flex min-h-[100dvh] flex-col">
      <Topo onBack={onBack} preenchidas={3} atual={4} />
      <section className="mx-auto flex w-full max-w-md flex-1 flex-col items-center px-5 pt-8 text-center anim-in">
        <div className="text-5xl" aria-hidden>🎉</div>
        <h1 className="mt-3 text-[30px] font-extrabold">Metade do caminho!</h1>
        <p className="mt-2 text-lg">Suas respostas me ajudam a montar um direcionamento só seu, e não um discurso pronto.</p>
        <div className="mt-5"><Chips /></div>
        <div className="mt-5 w-full space-y-3">
          <h2 className="text-2xl font-extrabold leading-tight">Veja os contatos chegando ao WhatsApp</h2>
          <p className="text-lg">Um registro real de pessoas entrando em contato com um negócio.</p>
          <QuizVideo media={QUIZ_VIDEOS.whatsapp} />
        </div>
        <div className="mt-6 w-full"><BotaoVerde onClick={onNext}>CONTINUAR <ArrowRight aria-hidden /></BotaoVerde></div>
      </section>
    </main>
  );
}

function Contato({ nome, setNome, tel, setTel, onBack, onDone, respostas }: {
  nome: string; setNome: (v: string) => void; tel: string; setTel: (v: string) => void;
  onBack: () => void; onDone: (n: Nivel) => void; respostas: Respostas;
}) {
  const [aceite, setAceite] = useState(false);
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [modal, setModal] = useState(false);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    const n = nome.trim();
    if (n.length < 2 || n.length > 100) return setErro("Digite o seu nome.");
    if (!telefoneValido(tel)) return setErro("Digite o WhatsApp com DDD (10 ou 11 números).");
    if (!aceite) return setErro("Para continuar, marque que concorda em ser contatado.");
    setErro(""); setEnviando(true);
    const nivel = nivelDe(respostas);
    let utm: Record<string, string> = {};
    try { utm = JSON.parse(sessionStorage.getItem(STORE + "-utm") || "{}"); } catch { /* */ }
    const { error } = await supabase.from("leads").insert({
      nome: n, whatsapp: tel.replace(/\D/g, ""),
      segmento: respostas.segmento ?? "", desafio: respostas.desafio ?? "", faturamento: respostas.faturamento ?? "",
      investimento: respostas.investimento ?? "", atendimento: respostas.atendimento ?? "", prazo: respostas.prazo ?? "",
      pontuacao: pontuar(respostas), nivel,
      utm_source: utm["utm_source"] ?? null, utm_medium: utm["utm_medium"] ?? null, utm_campaign: utm["utm_campaign"] ?? null,
      utm_content: utm["utm_content"] ?? null, utm_term: utm["utm_term"] ?? null, fbclid: utm["fbclid"] ?? null,
      consentimento: true, texto_consentimento_versao: TEXTO_CONSENTIMENTO_VERSAO,
    });
    setEnviando(false);
    if (error) { setErro("Não consegui salvar agora. Confira sua internet e tente de novo."); return; }
    setNome(n);
    onDone(nivel);
  }

  const campo = "h-14 w-full rounded-2xl border-2 border-border bg-card px-4 text-lg focus:border-primary focus:outline-none focus:ring-4 focus:ring-ring/30";
  return (
    <main className="flex min-h-[100dvh] flex-col">
      <Topo onBack={onBack} preenchidas={7} atual={7} />
      <form onSubmit={enviar} noValidate className="mx-auto flex w-full max-w-md flex-1 flex-col gap-4 px-5 pt-6 anim-in">
        <h1 className="text-[28px] font-extrabold leading-tight">Quase lá! Para onde envio o seu direcionamento?</h1>
        <label className="flex flex-col gap-1.5 text-base font-semibold">Seu nome
          <input className={campo} value={nome} onChange={(e) => setNome(e.target.value)} autoComplete="given-name" maxLength={100} />
        </label>
        <label className="flex flex-col gap-1.5 text-base font-semibold">Seu WhatsApp (com DDD)
          <input className={campo} value={tel} onChange={(e) => setTel(mascaraTelefone(e.target.value))} inputMode="numeric" autoComplete="tel-national" placeholder="(11) 91234-5678" />
        </label>
        <label className="flex items-start gap-3 text-base">
          <input type="checkbox" checked={aceite} onChange={(e) => setAceite(e.target.checked)} className="mt-1 h-6 w-6 shrink-0 accent-primary" />
          <span>Concordo em ser contatado pelo WhatsApp e com a{" "}
            <button type="button" onClick={() => setModal(true)} className="font-semibold text-primary underline">Política de Privacidade</button>
          </span>
        </label>
        {erro && <p role="alert" className="flex items-center gap-2 rounded-xl bg-destructive/10 p-3 text-base font-semibold text-destructive"><AlertTriangle size={20} aria-hidden />{erro}</p>}
        <BotaoVerde type="submit" disabled={enviando}>{enviando ? <Loader2 className="animate-spin" aria-hidden /> : null} VER MEU DIAGNÓSTICO <ArrowRight aria-hidden /></BotaoVerde>
        <div className="mt-auto"><Rodape /></div>
      </form>
      {modal && <Politica onClose={() => setModal(false)} />}
    </main>
  );
}

function Politica({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    ref.current?.focus();
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k); return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-foreground/60 p-3 sm:items-center" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-labelledby="pol-t" onClick={(e) => e.stopPropagation()} className="max-h-[85dvh] w-full max-w-md overflow-y-auto rounded-2xl bg-card p-5 anim-in">
        <div className="flex items-center justify-between">
          <h2 id="pol-t" className="text-xl font-extrabold">Política de Privacidade</h2>
          <button ref={ref} onClick={onClose} aria-label="Fechar" className="flex h-11 w-11 items-center justify-center rounded-full hover:bg-muted"><X aria-hidden /></button>
        </div>
        {/* PLACEHOLDER: substituir pelo texto final revisado */}
        <div className="mt-3 space-y-3 text-base">
          <p><b>Responsável:</b> Clayverson Demontier [PLACEHOLDER: CPF/CNPJ e cidade].</p>
          <p><b>Para que uso seus dados:</b> seu nome, WhatsApp e respostas servem só para eu te chamar no WhatsApp com o direcionamento do seu caso.</p>
          <p><b>Medição de anúncios:</b> esta página usa o Pixel da Meta para contar visitas e etapas concluídas, sem enviar seu nome ou telefone.</p>
          <p><b>Por quanto tempo guardo:</b> [PLACEHOLDER: prazo de guarda, ex.: 12 meses].</p>
          <p><b>Seus direitos:</b> você pode pedir para ver, corrigir ou apagar seus dados a qualquer momento pelo contato [PLACEHOLDER: e-mail ou WhatsApp].</p>
        </div>
      </div>
    </div>
  );
}

function Analise({ onDone }: { onDone: () => void }) {
  const itens = ["Entendendo seu segmento", "Avaliando seu momento", "Montando seu direcionamento"];
  const [n, setN] = useState(0);
  const done = useRef(onDone);
  done.current = onDone;
  useEffect(() => {
    const t = [700, 1500, 2200].map((ms, i) => setTimeout(() => setN(i + 1), ms));
    const fim = setTimeout(() => done.current(), 2500);
    return () => { t.forEach(clearTimeout); clearTimeout(fim); };
  }, []);
  return (
    <main className="flex min-h-[100dvh] items-center justify-center px-5">
      <div className="w-full max-w-md text-center anim-in" aria-live="polite">
        <Loader2 size={48} className="mx-auto animate-spin text-primary" aria-hidden />
        <h1 className="mt-4 text-[28px] font-extrabold">Analisando suas respostas…</h1>
        <ul className="mt-6 space-y-3 text-left">
          {itens.map((t, i) => (
            <li key={t} className={`flex items-center gap-3 rounded-2xl border-2 p-4 text-lg font-semibold transition-colors ${i < n ? "border-success bg-success/10" : "border-border bg-card text-muted-foreground"}`}>
              {i < n ? <Check className="text-success" aria-hidden /> : <Loader2 className="animate-spin" aria-hidden />}{t}
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}

function Medidor({ nivel }: { nivel: Nivel }) {
  const ang = nivel === "FRIO" ? -60 : nivel === "MORNO" ? 0 : 60;
  const arc = (a1: number, a2: number) => {
    const r = 80, cx = 100, cy = 100;
    const p = (a: number) => [cx + r * Math.cos(((a - 180) * Math.PI) / 180), cy + r * Math.sin(((a - 180) * Math.PI) / 180)];
    const [x1, y1] = p(a1), [x2, y2] = p(a2);
    return `M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`;
  };
  return (
    <svg viewBox="0 0 200 115" className="mx-auto w-56" role="img" aria-label={`Medidor: nível ${nivel.toLowerCase()}`}>
      <path d={arc(0, 58)} stroke="var(--destructive)" strokeWidth="18" fill="none" />
      <path d={arc(61, 119)} stroke="var(--warning)" strokeWidth="18" fill="none" />
      <path d={arc(122, 180)} stroke="var(--success)" strokeWidth="18" fill="none" />
      <g style={{ transform: `rotate(${ang}deg)`, transformOrigin: "100px 100px", transition: "transform 600ms ease-out" }}>
        <line x1="100" y1="100" x2="100" y2="34" stroke="var(--foreground)" strokeWidth="5" strokeLinecap="round" />
      </g>
      <circle cx="100" cy="100" r="8" fill="var(--foreground)" />
    </svg>
  );
}

function Resultado({ nome, telefone, respostas, nivel }: { nome: string; telefone: string; respostas: Respostas; nivel: Nivel }) {
  const [erroContato, setErroContato] = useState("");
  const info = NIVEL_INFO[nivel];
  const lista = insights(respostas);
  const abrirWhats = () => {
    if (!/^55\d{10,11}$/.test(WHATSAPP_NUMBER.replace(/\D/g, ""))) { setErroContato("O contato está sendo configurado. Tente novamente em instantes."); return; }
    // O site mede a abertura do WhatsApp, não confirma o envio da mensagem.
    track("track", "Lead", { nivel });
    const url = linkWhatsApp(mensagemWhatsApp(nome, respostas, nivel, telefone));
    setTimeout(() => { window.location.href = url; }, 200);
  };
  return (
    <main className="min-h-[100dvh]">
      <section className="mx-auto flex max-w-md flex-col gap-4 px-5 pt-8 anim-in">
        <Medidor nivel={nivel} />
        <h1 className="text-center text-[28px] font-extrabold leading-tight">
          {nome}, seu momento: <span className={nivel === "QUENTE" ? "text-success" : nivel === "MORNO" ? "text-primary" : "text-destructive"}>{info.titulo}</span>
        </h1>
        <p className="text-center text-lg">{info.texto}</p>
        {lista.length > 0 && (
          <div className="rounded-2xl border-2 border-border bg-card p-4">
            <h2 className="text-lg font-extrabold">O que eu vi nas suas respostas</h2>
            <ul className="mt-2 space-y-2">
              {lista.map((i) => (
                <li key={i.texto} className="flex gap-2 text-base">
                  {i.tipo === "alerta" ? <AlertTriangle size={22} className="shrink-0 text-destructive" aria-hidden /> : <Target size={22} className="shrink-0 text-primary" aria-hidden />}
                  <span>{i.texto}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        <section aria-label="Depoimento de cliente" className="space-y-3 rounded-2xl border-2 border-border bg-card p-4">
          <h2 className="text-center text-2xl font-extrabold leading-tight">Quem já trabalhou comigo conta</h2>
          <p className="text-center text-lg">Ouça o depoimento de um cliente de moda masculina sobre o trabalho que fizemos juntos.</p>
          <QuizVideo media={QUIZ_VIDEOS.depoimento} />
        </section>
        <div className="rounded-2xl border-2 border-success bg-success/10 p-5">
          <h2 className="text-2xl font-extrabold leading-tight">Você concluiu o quiz e tem direito a uma consultoria gratuita comigo.</h2>
          <p className="mt-3 text-lg">Vamos olhar a estrutura atual do seu negócio, seus anúncios e os pontos que podem melhorar para atrair mais clientes e aproveitar melhor as oportunidades de venda.</p>
          <p className="mt-3 text-lg font-semibold">Entre em contato para combinarmos nossa reunião.</p>
        </div>
        <BotaoVerde onClick={abrirWhats}><MessageCircle className="shrink-0" aria-hidden /> QUERO MINHA CONSULTORIA GRATUITA</BotaoVerde>
        {erroContato && <p role="alert" className="text-center text-base font-semibold text-destructive">{erroContato}</p>}
        <p className="text-center text-base text-muted-foreground">Seu resumo completo vai na mensagem do WhatsApp. Você não precisa responder tudo de novo.</p>
        <Rodape />
      </section>
    </main>
  );
}
