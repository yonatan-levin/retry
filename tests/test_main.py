# import asyncio
# from retry import Retry

# rules = {
#     "title": {
#         "selector": "h1",
#         "type": "css"
#     },
#     "content": {
#         "selector": "//article//p",
#         "type": "xpath",
#         "multiple": True
#     },
#     "links": {
#         "selector": "a",
#         "type": "css",
#         "attribute": "href",
#         "multiple": True
#     }
# }

# async def main():
#     scraper = Retry()
#     data = await scraper.scrape('https://example.com', rules)
#     print(scraper.output(data, format_type='json'))

# asyncio.run(main())