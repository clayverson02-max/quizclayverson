import { useEffect, useRef, useState } from "react";
import { Play, RotateCcw } from "lucide-react";
import type { QuizVideo as QuizVideoData } from "@/lib/media";

/** Baixa o vídeo apenas depois do toque; conserva som e controles nativos. */
export function QuizVideo({ media }: { media: QuizVideoData }) {
  const ref = useRef<HTMLVideoElement>(null);
  const [started, setStarted] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const video = ref.current;
    return () => {
      video?.pause();
      video?.removeAttribute("src");
      video?.load();
    };
  }, []);

  function start() {
    const video = ref.current;
    if (!video) return;
    setFailed(false);
    setStarted(true);
    // Iniciar dentro do gesto permite áudio no Safari do iPhone.
    video.src = media.src;
    video.load();
    void video.play().catch(() => {
      // Os controles continuam disponíveis se o navegador bloquear o play.
      if (video.error) setFailed(true);
    });
  }

  return (
    <div className="mx-auto w-full max-w-[17rem]">
      <div
        className="relative overflow-hidden rounded-2xl border border-border bg-navy shadow-lg"
        style={{ aspectRatio: media.aspectRatio }}
      >
        <video
          ref={ref}
          poster={media.poster}
          preload="none"
          playsInline
          controls={started && !failed}
          aria-label={media.title}
          className="absolute inset-0 h-full w-full object-contain"
          onError={() => setFailed(true)}
        />
        {(!started || failed) && (
          <button
            type="button"
            onClick={start}
            aria-label={`${failed ? "Tentar reproduzir novamente" : "Assistir"}: ${media.title}`}
            className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-navy/35 p-4 text-center text-navy-foreground focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-inset focus-visible:ring-warning"
          >
            <span className="flex h-20 w-20 items-center justify-center rounded-full bg-success text-success-foreground shadow-xl">
              {failed ? (
                <RotateCcw size={36} aria-hidden />
              ) : (
                <Play size={36} fill="currentColor" aria-hidden />
              )}
            </span>
            <span className="rounded-xl bg-navy px-4 py-3 text-lg font-extrabold">
              {failed ? "TENTAR NOVAMENTE" : "ASSISTIR COM SOM"}
            </span>
          </button>
        )}
      </div>
      {failed && (
        <p role="status" className="mt-3 text-center text-base font-semibold text-destructive">
          O vídeo não carregou. Confira sua conexão e tente novamente.
        </p>
      )}
    </div>
  );
}
