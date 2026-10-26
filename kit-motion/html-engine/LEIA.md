# Motor de motion graphics em HTML (aprovado pelo dono em 26/10/2026)

Padrão que o dono aprovou ("perfeito"): cenas em HTML/CSS animadas com Web Animations API, renderizadas quadro a quadro com Playwright (30 fps, 1080x1920) e juntadas com ffmpeg.

- plataforma.html: estilo Apple/minimal (claro e escuro), celular com a área de membros, filtros, prancheta tática desenhando, anel 3D, bônus e CTA. Transições: máscara circular, whip, subida e zoom com flash. Legendas palavra por palavra.
- oferta.html: oferta pesada no formato "¿Ya imaginaste...?" (?v=jugador|entrenador&vo=[{text,dur}]). Tipografia Inter Display Black condensada, slam de palavras, tremida de câmera, tela dividida, holofote, mosaico 3D de vídeos com contador, cartas de bônus, preço riscado, selo de garantia e faixas correndo.
- Narração: gen.tts (Piper es_MX; masculino: claude-high e ald-medium), atempo 1.08 para energia, tempo das cenas = duração da fala + 0,6 s.
- Áudio: audio_*.py (beat original, risers e impactos nas trocas, cliques e pops sincronizados, música abaixa quando a voz fala).
- Clips reais: kit-futbol/clips (sequências jpg); w1 = gravação da área de membros real (FÚTBOL PRO).

Regras: os elementos visuais acompanham o que a narração está dizendo naquele momento (palavra falada = elemento na tela); variar cenário, hook e formato a cada vídeo; nunca repetir o mesmo visual; nada de urgência falsa nem números inventados.
