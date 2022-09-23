import asyncio
import json
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        with open('data.json', 'r') as f:
            data = json.load(f)
            print (data)

        self.render("template.html", title="My title", items=data[0])

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

async def main():
    app = make_app()
    app.listen(8888)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())