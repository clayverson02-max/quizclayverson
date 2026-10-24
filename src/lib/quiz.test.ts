import { describe, it, expect } from "vitest";
import { nivelDe, pontuar, mascaraTelefone, telefoneValido, insights } from "./quiz";

const base = {
  segmento: "Outro",
  desafio: "Pago caro por cada contato",
  faturamento: "R$ 100 a 300 mil", // 4
  investimento: "R$ 10.000 a 30.000", // 4
  atendimento: "Uma equipe de vendas", // 3
  prazo: "O quanto antes (esta semana)", // 3
};

describe("pontuação e nível", () => {
  it("máximo de 16 pontos", () => {
    expect(pontuar({ ...base, faturamento: "Acima de R$ 300 mil", investimento: "Acima de R$ 30.000" })).toBe(16);
  });
  it("14 pontos é QUENTE", () => expect(nivelDe(base)).toBe("QUENTE"));
  it("investimento menor que R$ 1.000 é sempre FRIO", () =>
    expect(nivelDe({ ...base, faturamento: "Acima de R$ 300 mil", investimento: "Menos de R$ 1.000" })).toBe("FRIO"));
  it("5 pontos é FRIO", () =>
    expect(nivelDe({ ...base, faturamento: "Até R$ 10 mil", investimento: "R$ 1.000 a 3.000", atendimento: "Ainda não tenho ninguém", prazo: "Nos próximos 30 dias" })).toBe("FRIO"));
  it("6 pontos é MORNO", () =>
    expect(nivelDe({ ...base, faturamento: "Até R$ 10 mil", investimento: "R$ 1.000 a 3.000", atendimento: "Eu mesmo, pelo WhatsApp", prazo: "Nos próximos 30 dias" })).toBe("MORNO"));
  it("10 pontos é MORNO e 11 é QUENTE", () => {
    const dez = { ...base, faturamento: "R$ 30 a 100 mil", investimento: "R$ 3.000 a 10.000", atendimento: "Eu mesmo, pelo WhatsApp", prazo: "O quanto antes (esta semana)" };
    expect(pontuar(dez)).toBe(10);
    expect(nivelDe(dez)).toBe("MORNO");
    expect(nivelDe({ ...dez, atendimento: "Uma atendente ou recepção" })).toBe("QUENTE");
  });
});

describe("telefone", () => {
  it("aceita 10 ou 11 dígitos", () => {
    expect(telefoneValido("(11) 91234-5678")).toBe(true);
    expect(telefoneValido("(11) 1234-5678")).toBe(true);
    expect(telefoneValido("(11) 1234-567")).toBe(false);
  });
  it("aplica máscara", () => expect(mascaraTelefone("11912345678")).toBe("(11) 91234-5678"));
});

describe("o que eu vi", () => {
  it("no máximo 3 itens", () => {
    expect(insights({ ...base, atendimento: "Ainda não tenho ninguém", investimento: "Menos de R$ 1.000" })).toHaveLength(3);
  });
});
