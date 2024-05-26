import re
from typing import IO, List, Optional

from pydantic import BaseModel

from apigen.helpers import formatted

Row = List[str]


class ParseError(Exception):
    pass


class ApiElement(BaseModel):
    section: str
    title: str
    description: str
    table_header: Optional[Row] = None
    table: Optional[List[Row]] = None
    ul: Optional[List[str]] = None

    def is_method(self) -> bool:
        return (
            self.table_header == ["Parameter", "Type", "Required", "Description"]
            if self.table_header is not None
            else "method " in self.description.lower()
        )

    def is_object(self) -> bool:

        return (
            self.table_header == ["Field", "Type", "Description"]
            if self.table_header is not None
            else (" " not in self.title and "holds no information" in self.description)
        )

    def is_union(self) -> bool:
        if not self.ul:
            return False
        if " " in self.title:
            return False
        for s in self.ul:
            if " " in s:
                return False
        return True


class ApiType(BaseModel):
    py_annotation: str

    @staticmethod
    def parse(*, original_type: str, optional: bool) -> "ApiType":
        is_list = False
        is_list_of_list = False
        types = []

        if original_type.startswith("Array of Array of"):
            types.append(original_type[18:])
            is_list = True
            is_list_of_list = True
        elif original_type.startswith("Array of"):
            types.append(original_type[9:])
            is_list = True
        elif " or " in original_type:
            types = original_type.split(" or ")
        else:
            types.append(original_type)

        types = [
            (
                "int"
                if t == "Integer"
                else (
                    "int"
                    if t == "Int"
                    else (
                        "bool"
                        if t == "Boolean"
                        else (
                            "bool" if t == "True" else "str" if t == "String" else "float" if t == "Float" else f"'{t}'"
                        )
                    )
                )
            )
            for t in types
        ]

        if len(types) > 1:
            parsed = f"Union[{', '.join(types)}]"
        else:
            parsed = types[0]

        if is_list:
            parsed = f"List[{parsed}]"

        if is_list_of_list:
            parsed = f"List[{parsed}]"

        if optional:
            parsed = f"Optional[{parsed}]"

        return ApiType(py_annotation=parsed)

    @staticmethod
    def parse_return_type(description: str) -> "ApiType":
        def t_re(pattern) -> Optional[str]:
            m = re.search(pattern, description, re.UNICODE)
            if m:
                try:
                    return m.group(1)
                except IndexError:
                    return None
            return None

        if "Returns True on success" in description:
            parsed = "bool"
        elif "On success, True is returned" in description:
            parsed = "bool"
        elif "Message is returned, otherwise True is returned" in description:
            parsed = "Union['Message', bool]"
        elif re.search(r"eturns[\w\s]+as String on success", description, re.UNICODE):
            parsed = "str"
        elif (t := t_re(r"eturns an Array of (\w+)")) or (  # noqa
            t := t_re(r"success, an array of (\w+)[\w\s]+returned")
        ):
            if t == "Messages":
                t = "Message"  # misprint in docs
            parsed = f"List['{t}']"
        elif (
            (t := t_re(r"eturns a ([A-Z]\w+) object"))  # noqa
            or (t := t_re(r"success,[\w\s]+ ([A-Z]\w+)[\w\s]+is returned"))  # noqa
            or (t := t_re(r"eturns[\w\s]+ as a? ?([A-Z]\w+) object"))  # noqa
            or (t := t_re(r"eturns the ([A-Z]\w+) [\w\s]+on success"))  # noqa
            or (t := t_re(r"eturns the[\w\s]+([A-Z]\w+) on success"))  # noqa
            or (t := t_re(r"eturns ([A-Z]\w+) on success"))  # noqa
            or (t := t_re(r"eturns[\w\s]+in form of a ([A-Z]\w+) object"))
        ):
            if t == "Int":
                parsed = "int"
            else:
                parsed = f"'{t}'"
        else:
            parsed = "Any"

        return ApiType(
            py_annotation=parsed,
        )


class ApiParam(BaseModel):
    name: str
    api_type: ApiType
    description: str
    optional: bool

    @staticmethod
    def parse(row: Row) -> "ApiParam":
        assert len(row) == 4
        if row[2] not in ["Yes", "Optional"]:
            raise ParseError(f"Can not parse param {row[0]}, {row[2]} should be 'Yes' or 'Optional'")
        optional = row[2] == "Optional"
        return ApiParam(
            name=row[0],
            api_type=ApiType.parse(
                original_type=row[1],
                optional=optional,
            ),
            description=row[3],
            optional=optional,
        )


class ApiMethod(BaseModel):
    name: str
    params: List[ApiParam]
    return_type: ApiType
    description: str

    @staticmethod
    def parse(el: ApiElement) -> "ApiMethod":
        return ApiMethod(
            name=el.title,
            params=([ApiParam.parse(row) for row in el.table] if el.table is not None else []),
            return_type=ApiType.parse_return_type(el.description),
            description=el.description,
        )

    def gen(self, f, is_async: bool = False):
        params = sorted(self.params, key=lambda p: 1 if p.optional else -1)
        sig = (
            "            self,\n"
            + ("            *,\n" if params else "")
            + (
                "".join(
                    f"            {p.name}: {p.api_type.py_annotation}"
                    + (" = None" if p.optional else "")
                    + ","
                    + ("  # noqa" if p.name in ["type", "format"] else "")
                    + "\n"
                    for p in params
                )
            )
        )
        f.write(
            f"    {'async ' if is_async else ''}def {self.name}(\n{sig}    ) -> {self.return_type.py_annotation}:\n"
        )
        f.write('        """\n')
        f.write(formatted(self.description, "        ") + "\n")
        if params:
            f.write("\n")
        for p in params:
            desc = formatted(p.description, "            ", "") + "\n"
            f.write(f"        :param {p.name}: {desc}")
        f.write('        """\n        pass\n\n')


class ApiField(BaseModel):
    name: str
    api_type: ApiType
    description: str
    optional: bool

    @staticmethod
    def parse(row: Row) -> "ApiField":
        assert len(row) == 3
        optional = row[2].startswith("Optional")

        return ApiField(
            name=row[0],
            api_type=ApiType.parse(
                original_type=row[1],
                optional=optional,
            ),
            description=row[2],
            optional=optional,
        )

    def gen(self, f):
        name = self.name if self.name != "from" else "from_"
        alias = 'alias="from"' if self.name == "from" else ""
        default = f"None" if self.optional else ""
        eq = f" = Field({default}, {alias})" if default and alias else f" = {default}" if default else ""

        f.write(f"    {name}: {self.api_type.py_annotation}{eq}\n")
        f.write('    """ ')
        f.write(formatted(self.description, "    ", ""))
        f.write(' """\n\n')


class ApiObject(BaseModel):
    name: str
    fields: List[ApiField]
    description: str

    @staticmethod
    def parse(el: ApiElement) -> "ApiObject":
        return ApiObject(
            name=el.title,
            fields=([ApiField.parse(row) for row in el.table] if el.table is not None else []),
            description=el.description,
        )

    def gen(self, f: IO):
        f.write(f"class {self.name}(BaseModel):\n")
        f.write('    """\n')
        f.write(formatted(self.description, "    ") + "\n")
        f.write('    """\n')

        if self.fields:
            f.write("\n")
            fields = sorted(self.fields, key=lambda f: 1 if f.optional else -1)
            for fld in fields:
                fld.gen(f)
        else:
            f.write("    pass\n\n")

        f.write("\n")


class ApiUnion(BaseModel):
    name: str
    description: str
    union: List[str]

    @staticmethod
    def parse(el: ApiElement) -> "ApiUnion":
        return ApiUnion(
            name=el.title,
            description=el.description,
            union=el.ul,
        )

    def gen(self, f):
        f.write('"""\n')
        f.write(formatted(self.description) + "\n")
        f.write('"""\n')
        res = "".join(f"    {l},\n" for l in self.union)
        f.write(f"{self.name} = Union[\n{res}]\n\n")


class Api(BaseModel):
    objects: List[ApiObject]
    methods: List[ApiMethod]
    unions: List[ApiUnion]
    ignored: List[ApiElement]

    @staticmethod
    def parse(els: List[ApiElement]) -> "Api":
        api = Api(
            objects=[],
            methods=[],
            unions=[],
            ignored=[],
        )
        for el in els:
            try:
                if el.is_object():
                    api.objects.append(ApiObject.parse(el))
                elif el.is_method():
                    api.methods.append(ApiMethod.parse(el))
                elif el.is_union():
                    api.unions.append(ApiUnion.parse(el))
                else:
                    api.ignored.append(el)
            except ParseError as e:
                print(f"Warning: parse error {e}")
                api.ignored.append(el)

        return api

    def gen(self, f):
        f.write(
            "from typing import Any, List, Optional, Protocol, Union\n\nfrom pydantic import BaseModel, Field\n\n\n"
        )
        for o in self.objects:
            o.gen(f)
        for u in self.unions:
            u.gen(f)

        f.write(
            '"""InputFile should be file-like object, supported only in api calls, not models"""\nInputFile = Any\n\n'
        )

        for o in self.objects:
            f.write(f"{o.name}.update_forward_refs()\n\n")

        f.write("\n")

        f.write("class Teleapi(Protocol):\n")
        for m in self.methods:
            m.gen(f)

        f.write("\n")

        f.write("class TeleapiAsync(Protocol):\n")
        for m in self.methods:
            m.gen(f, True)

        f.write("# EOF\n")
