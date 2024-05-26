from apigen.gen import gen
from apigen.models import Api
from apigen.parse import load_apidoc, parse_apidoc

parsed = parse_apidoc(load_apidoc("https://core.telegram.org/bots/api"))
api = Api.parse(parsed)
gen(api)
print("Done")
