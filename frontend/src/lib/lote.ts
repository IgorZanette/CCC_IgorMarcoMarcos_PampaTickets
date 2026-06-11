// Disponibilidade de lote para o fluxo de compra do participante.
// Espelha as regras de pedido_service.criar no backend: um lote só é comprável se
// estiver ativo, dentro da janela de venda e com estoque. Usar isto no front evita
// que o participante selecione/compre um lote que o backend recusaria com 409.

import type { Lote } from "../api/lotes";

export type MotivoIndisponivel = "esgotado" | "encerrado" | "nao_iniciado" | "inativo";

export type DisponibilidadeLote = {
  disponivel: boolean;
  motivo: MotivoIndisponivel | null;
  rotulo: string | null;
  restantes: number;
};

const ROTULOS: Record<MotivoIndisponivel, string> = {
  esgotado: "Esgotado",
  encerrado: "Vendas encerradas",
  nao_iniciado: "Em breve",
  inativo: "Indisponível",
};

export const avaliarLote = (
  lote: Lote,
  agora: Date = new Date(),
): DisponibilidadeLote => {
  const restantes = lote.quantidade_disponivel;
  const esgotado = restantes <= 0;
  const inativo = !lote.ativo;
  // As datas vêm em UTC (ISO com offset); a comparação entre instantes independe de
  // fuso, então não precisa da conversão de São Paulo usada só na exibição.
  const naoIniciado = agora < new Date(lote.data_inicio_venda);
  const encerrado = agora > new Date(lote.data_fim_venda);

  // Precedência do rótulo pela informação mais útil ao usuário (difere da ordem de
  // checagem do backend, que não importa para o booleano `disponivel`).
  const motivo: MotivoIndisponivel | null = esgotado
    ? "esgotado"
    : encerrado
      ? "encerrado"
      : naoIniciado
        ? "nao_iniciado"
        : inativo
          ? "inativo"
          : null;

  return {
    disponivel: motivo === null,
    motivo,
    rotulo: motivo ? ROTULOS[motivo] : null,
    restantes,
  };
};
