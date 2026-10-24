import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/api/meta-events")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const { handleMetaEvent } = await import("@/server/meta-events.server");
        return handleMetaEvent(request);
      },
    },
  },
});
