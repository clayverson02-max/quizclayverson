// Troque os caminhos aqui quando houver novos vídeos e capas.
// Originais enviados pelo proprietário na raiz do repositório.
export const QUIZ_VIDEOS = {
  whatsapp: {
    src: "/videos/whatsapp-contatos.mp4",
    poster: "/images/whatsapp-contatos.webp",
    title: "Contatos chegando ao WhatsApp",
    aspectRatio: "29 / 52",
  },
  depoimento: {
    src: "/videos/depoimento-cliente.mp4",
    poster: "/images/depoimento-cliente.webp",
    title: "Depoimento de um cliente de moda masculina",
    aspectRatio: "9 / 16",
  },
} as const;

export type QuizVideo = (typeof QUIZ_VIDEOS)[keyof typeof QUIZ_VIDEOS];
