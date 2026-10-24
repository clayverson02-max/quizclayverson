import { PIXEL_ID } from "@/lib/quiz";

const names = new Set([
  "PageView",
  "Lead",
  "Contact",
  "Quiz_Start",
  "Quiz_Step",
  "Quiz_Quente",
  "Quiz_Morno",
  "Quiz_Frio",
]);
let cachedToken: { value: string; expires: number } | undefined;

async function token() {
  if (process.env["META_ACCESS_TOKEN"]) return process.env["META_ACCESS_TOKEN"];
  if (cachedToken && cachedToken.expires > Date.now()) return cachedToken.value;
  const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
  const client = supabaseAdmin as unknown as {
    rpc: (name: string) => PromiseLike<{ data: unknown; error: unknown }>;
  };
  const result = await client.rpc("quiz_meta_token");
  if (result.error || typeof result.data !== "string" || !result.data) return undefined;
  cachedToken = { value: result.data, expires: Date.now() + 300_000 };
  return result.data;
}

export async function handleMetaEvent(request: Request) {
  const headers = { "Cache-Control": "no-store" };
  const origin = new URL(request.url).origin;
  if (request.headers.get("origin") !== origin) return new Response(null, { status: 403 });
  if (!request.headers.get("content-type")?.includes("application/json"))
    return new Response(null, { status: 415 });
  const body = await request.text();
  if (body.length > 4096) return new Response(null, { status: 413 });
  let event: {
    name?: string;
    eventId?: string;
    sourceUrl?: string;
    params?: Record<string, unknown>;
  };
  try {
    event = JSON.parse(body);
  } catch {
    return new Response(null, { status: 400 });
  }
  if (!names.has(event.name ?? "") || !/^[a-zA-Z0-9-]{8,100}$/.test(event.eventId ?? ""))
    return new Response(null, { status: 400 });
  try {
    const accessToken = await token();
    if (!accessToken) return Response.json({ ok: false }, { status: 503, headers });
    const cookies = new Map(
      (request.headers.get("cookie") ?? "").split(";").map((v) => {
        const i = v.indexOf("=");
        return [v.slice(0, i).trim(), v.slice(i + 1)];
      }),
    );
    const userData: Record<string, string> = {
      client_user_agent: request.headers.get("user-agent") ?? "",
    };
    const ip =
      request.headers.get("cf-connecting-ip") ??
      request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
    if (ip) userData["client_ip_address"] = ip;
    for (const key of ["fbp", "fbc"]) {
      const value = cookies.get("_" + key);
      if (value && /^fb\.[0-9.]+\.[a-zA-Z0-9_-]+$/.test(value)) userData[key] = value;
    }
    const source = new URL(event.sourceUrl ?? "/", origin);
    if (source.origin !== origin) return new Response(null, { status: 400 });
    const params: Record<string, string> = {};
    for (const key of ["etapa", "nivel"])
      if (typeof event.params?.[key] === "string")
        params[key] = String(event.params[key]).slice(0, 80);
    const response = await fetch(`https://graph.facebook.com/v25.0/${PIXEL_ID}/events`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        data: [
          {
            event_name: event.name,
            event_time: Math.floor(Date.now() / 1000),
            event_id: event.eventId,
            action_source: "website",
            event_source_url: source.origin + source.pathname,
            user_data: userData,
            custom_data: params,
          },
        ],
      }),
      signal: AbortSignal.timeout(5000),
    });
    return Response.json({ ok: response.ok }, { status: response.ok ? 200 : 502, headers });
  } catch {
    return Response.json({ ok: false }, { status: 503, headers });
  }
}
