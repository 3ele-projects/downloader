import asyncio
import json
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        with open('data.json', 'r') as f:
            data = json.load(f)
         #   print (data)
            mylist =[]
            
            for site in data:
                for key, value in site.items():
                    
                    domain = {
                        'domain' : key,
                        'values' : value
                    }
                    domain['alert'] = False  
                    if len(value['messages']['errors']) > 0:
                        domain['alert'] = True    
                    mylist.append(domain)
                    
        self.render("template.html", title="Downloads", items=mylist)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

async def main():
    app = make_app()
    app.listen(8889)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())