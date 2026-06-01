from aiohttp import web
import os

async def handle(request):
    return web.Response(text="Bot is Alive!")

app = web.Application()
app.router.add_get('/', handle)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
