CREATE TABLE public.leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  criado_em timestamptz NOT NULL DEFAULT now(),
  nome text NOT NULL,
  whatsapp text NOT NULL,
  segmento text NOT NULL,
  desafio text NOT NULL,
  faturamento text NOT NULL,
  investimento text NOT NULL,
  atendimento text NOT NULL,
  prazo text NOT NULL,
  pontuacao integer NOT NULL,
  nivel text NOT NULL,
  utm_source text, utm_medium text, utm_campaign text, utm_content text, utm_term text, fbclid text,
  consentimento boolean NOT NULL,
  texto_consentimento_versao text NOT NULL,
  CONSTRAINT leads_consent CHECK (consentimento = true),
  CONSTRAINT leads_nome_len CHECK (char_length(nome) BETWEEN 1 AND 100),
  CONSTRAINT leads_wa CHECK (whatsapp ~ '^[0-9]{10,11}$'),
  CONSTRAINT leads_nivel CHECK (nivel IN ('QUENTE','MORNO','FRIO'))
);
GRANT INSERT ON public.leads TO anon, authenticated;
GRANT ALL ON public.leads TO service_role;
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Visitantes podem enviar lead com aceite" ON public.leads FOR INSERT TO anon, authenticated WITH CHECK (consentimento = true);