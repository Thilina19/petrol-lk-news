export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      if (url.pathname === "/") url.pathname = "/index.html";
      return await env.ASSETS.fetch(new Request(url, request));
    } catch (e) {
      return new Response(String(e?.stack || e), { status: 500 });
    }
  },
};
