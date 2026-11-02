#!/usr/bin/env python3
"""Compare two versions of an API contract and classify each change. Standard library only.

Usage: python scripts/contract_diff.py OLD.json NEW.json [--mode request|response|both] [--json]
Inputs: OpenAPI 3.x documents or plain JSON Schema documents, both as JSON (convert YAML to JSON first).
Exit codes: 0 no BREAKING change, 1 at least one BREAKING change, 2 bad input.

Classes:
  BREAKING  an existing client or consumer that followed the old contract can fail
  RISKY     can fail some clients (exhaustive switches, strict validators, generated SDK names)
  SAFE      additive or loosening in the direction that cannot hurt a conforming client

Direction matters. In a request (what clients send) adding a required field is breaking and removing one is not.
In a response (what clients read) removing a field is breaking and adding one is not. For OpenAPI the direction
comes from where the schema sits. For a plain JSON Schema use --mode (default both: every change is judged
in both directions and the stricter class wins).

Resolves local $ref ("#/...") only; external references are skipped and reported as RISKY. Swagger 2 is not supported.
"""
import json, sys

METHODS = ("get", "put", "post", "delete", "patch", "head", "options", "trace")
ORDER = {"BREAKING": 0, "RISKY": 1, "SAFE": 2}
MAX_DEPTH = 14
LOWER_IS_TIGHTER = ("maximum", "maxLength", "maxItems", "maxProperties", "exclusiveMaximum")
HIGHER_IS_TIGHTER = ("minimum", "minLength", "minItems", "minProperties", "exclusiveMinimum")


class Diff:
    def __init__(self, old, new):
        self.old, self.new, self.found = old, new, []

    def add(self, level, where, msg):
        item = (level, where, msg)
        if item not in self.found:
            self.found.append(item)

    def resolve(self, doc, node, seen=()):
        while isinstance(node, dict) and "$ref" in node:
            ref = node["$ref"]
            if ref in seen:
                return {}
            seen += (ref,)
            if not isinstance(ref, str) or not ref.startswith("#/"):
                return {}
            cur = doc
            for part in ref[2:].split("/"):
                part = part.replace("~1", "/").replace("~0", "~")
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    return {}
            node = cur
        return node if isinstance(node, dict) else {}

    def flat(self, doc, schema):
        s = self.resolve(doc, schema)
        if "allOf" in s and isinstance(s["allOf"], list):
            merged = {k: v for k, v in s.items() if k != "allOf"}
            props, req = dict(merged.get("properties", {})), list(merged.get("required", []))
            for part in s["allOf"]:
                p = self.flat(doc, part)
                props.update(p.get("properties", {}))
                req += p.get("required", [])
                for k, v in p.items():
                    if k not in ("properties", "required"):
                        merged.setdefault(k, v)
            if props:
                merged["properties"] = props
            if req:
                merged["required"] = sorted(set(req))
            return merged
        return s

    @staticmethod
    def types(s):
        t = s.get("type")
        ts = set(t) if isinstance(t, list) else ({t} if isinstance(t, str) else set())
        if s.get("nullable") is True:
            ts.add("null")
        return ts

    def schema(self, o, n, where, mode, depth=0):
        """Compare two schemas. mode is 'request' or 'response'."""
        if depth > MAX_DEPTH:
            return
        if isinstance(o, dict) and "$ref" in o and not str(o["$ref"]).startswith("#/") or \
           isinstance(n, dict) and "$ref" in n and not str(n["$ref"]).startswith("#/"):
            self.add("RISKY", where, "external $ref cannot be compared")
            return
        o, n = self.flat(self.old, o), self.flat(self.new, n)
        ot, nt = self.types(o), self.types(n)
        if ot and nt and ot != nt:
            if "null" in nt and "null" not in ot and mode == "response":
                self.add("BREAKING", where, f"response can now be null (type {sorted(ot)} -> {sorted(nt)})")
            elif "null" in ot and "null" not in nt and mode == "request":
                self.add("BREAKING", where, f"request no longer accepts null (type {sorted(ot)} -> {sorted(nt)})")
            elif ot - {"null"} != nt - {"null"}:
                self.add("BREAKING", where, f"type changed {sorted(ot)} -> {sorted(nt)}")
            else:
                self.add("SAFE", where, f"nullability changed in the harmless direction ({sorted(ot)} -> {sorted(nt)})")
        # enum
        if "enum" in o or "enum" in n:
            oe, ne = o.get("enum"), n.get("enum")
            if oe is not None and ne is None:
                self.add("SAFE" if mode == "request" else "RISKY", where, "enum restriction removed")
            elif oe is None and ne is not None:
                self.add("BREAKING" if mode == "request" else "SAFE", where, "enum restriction added")
            elif oe is not None and ne is not None:
                removed = [v for v in oe if v not in ne]
                added = [v for v in ne if v not in oe]
                if removed:
                    self.add("BREAKING" if mode == "request" else "SAFE", where, f"enum values removed: {removed}")
                if added:
                    self.add("SAFE" if mode == "request" else "RISKY", where, f"enum values added: {added}" + (" (clients with an exhaustive switch can fail)" if mode == "response" else ""))
        # numeric and length limits
        for key in LOWER_IS_TIGHTER + HIGHER_IS_TIGHTER:
            a, b = o.get(key), n.get(key)
            if a == b or isinstance(a, bool) or isinstance(b, bool):
                continue
            tighter = (a is None and b is not None) or (a is not None and b is not None and ((key in LOWER_IS_TIGHTER and b < a) or (key in HIGHER_IS_TIGHTER and b > a)))
            if tighter:
                self.add("BREAKING" if mode == "request" else "SAFE", where, f"{key} tightened: {a} -> {b}")
            else:
                self.add("SAFE" if mode == "request" else "RISKY", where, f"{key} loosened: {a} -> {b}")
        for key in ("pattern", "format"):
            if o.get(key) != n.get(key):
                self.add("RISKY", where, f"{key} changed: {o.get(key)!r} -> {n.get(key)!r}")
        if o.get("default") != n.get("default"):
            self.add("RISKY", where, f"default changed: {o.get('default')!r} -> {n.get('default')!r}")
        # additionalProperties
        oa, na = o.get("additionalProperties", True), n.get("additionalProperties", True)
        if oa != na:
            if na is False and mode == "request":
                self.add("BREAKING", where, "additionalProperties set to false: unknown fields are now rejected")
            elif na is False:
                self.add("RISKY", where, "additionalProperties set to false")
            else:
                self.add("RISKY", where, f"additionalProperties changed: {oa!r} -> {na!r}")
        # object properties
        op, np_ = o.get("properties", {}), n.get("properties", {})
        oreq, nreq = set(o.get("required", [])), set(n.get("required", []))
        for name in sorted(set(op) | set(np_)):
            w = f"{where}.{name}"
            if name in op and name not in np_:
                if mode == "response":
                    self.add("BREAKING", w, "field removed from the response")
                elif na is False:
                    self.add("BREAKING", w, "field removed and unknown fields are rejected")
                else:
                    self.add("RISKY", w, "field removed from the request schema (clients may still send it)")
            elif name in np_ and name not in op:
                if mode == "request" and name in nreq:
                    self.add("BREAKING", w, "new required field in the request")
                else:
                    self.add("SAFE", w, "new optional field" if name not in nreq else "new field in the response")
            else:
                self.schema(op[name], np_[name], w, mode, depth + 1)
        for name in sorted(oreq | nreq):
            if name in op and name in np_:
                w = f"{where}.{name}"
                if mode == "request" and name in nreq and name not in oreq:
                    self.add("BREAKING", w, "field became required in the request")
                elif mode == "request" and name in oreq and name not in nreq:
                    self.add("SAFE", w, "field became optional in the request")
                elif mode == "response" and name in oreq and name not in nreq:
                    self.add("BREAKING", w, "field is no longer guaranteed in the response")
                elif mode == "response" and name in nreq and name not in oreq:
                    self.add("SAFE", w, "field is now guaranteed in the response")
        # arrays
        if "items" in o and "items" in n and isinstance(o["items"], dict) and isinstance(n["items"], dict):
            self.schema(o["items"], n["items"], where + "[]", mode, depth + 1)
        # composition
        for key in ("oneOf", "anyOf"):
            if key in o or key in n:
                ol, nl = o.get(key, []), n.get(key, [])
                if len(ol) != len(nl):
                    self.add("RISKY", where, f"{key} has {len(ol)} option(s) before and {len(nl)} after")
                else:
                    for i, (a, b) in enumerate(zip(ol, nl)):
                        self.schema(a, b, f"{where}.{key}[{i}]", mode, depth + 1)

    # ---- OpenAPI -------------------------------------------------------
    def params(self, doc, path_item, op):
        out = {}
        for src in (path_item.get("parameters", []), op.get("parameters", [])):
            for p in src:
                p = self.resolve(doc, p)
                if "name" in p:
                    out[(p.get("in", "query"), p["name"])] = p
        return out

    def content(self, o, n, where, mode):
        oc, nc = o.get("content", {}), n.get("content", {})
        for mt in sorted(set(oc) | set(nc)):
            w = f"{where}.{mt}"
            if mt in oc and mt not in nc:
                self.add("BREAKING", w, "media type removed")
            elif mt in nc and mt not in oc:
                self.add("SAFE", w, "media type added")
            elif "schema" in oc[mt] and "schema" in nc[mt]:
                self.schema(oc[mt]["schema"], nc[mt]["schema"], w, mode)

    def operation(self, pi_old, pi_new, op_old, op_new, where):
        if op_old.get("operationId") != op_new.get("operationId") and op_old.get("operationId"):
            self.add("RISKY", where, f"operationId changed {op_old.get('operationId')!r} -> {op_new.get('operationId')!r} (renames generated SDK methods)")
        if op_new.get("deprecated") and not op_old.get("deprecated"):
            self.add("RISKY", where, "operation marked deprecated")
        po, pn = self.params(self.old, pi_old, op_old), self.params(self.new, pi_new, op_new)
        for key in sorted(set(po) | set(pn)):
            w = f"{where}.param[{key[0]}:{key[1]}]"
            if key in po and key not in pn:
                self.add("RISKY", w, "parameter removed (clients that send it may now be rejected)")
            elif key in pn and key not in po:
                self.add("BREAKING" if pn[key].get("required") else "SAFE", w, "new required parameter" if pn[key].get("required") else "new optional parameter")
            else:
                if pn[key].get("required") and not po[key].get("required"):
                    self.add("BREAKING", w, "parameter became required")
                elif po[key].get("required") and not pn[key].get("required"):
                    self.add("SAFE", w, "parameter became optional")
                so, sn = po[key].get("schema"), pn[key].get("schema")
                if isinstance(so, dict) and isinstance(sn, dict):
                    self.schema(so, sn, w, "request")
        rb_o, rb_n = self.resolve(self.old, op_old.get("requestBody", {})), self.resolve(self.new, op_new.get("requestBody", {}))
        if rb_n and not rb_o:
            self.add("BREAKING" if rb_n.get("required") else "SAFE", where + ".requestBody", "request body added" + (" and required" if rb_n.get("required") else ""))
        elif rb_o and not rb_n:
            self.add("RISKY", where + ".requestBody", "request body removed")
        elif rb_o and rb_n:
            if rb_n.get("required") and not rb_o.get("required"):
                self.add("BREAKING", where + ".requestBody", "request body became required")
            self.content(rb_o, rb_n, where + ".requestBody", "request")
        ro, rn = op_old.get("responses", {}), op_new.get("responses", {})
        for code in sorted(set(ro) | set(rn)):
            w = f"{where}.response[{code}]"
            if code in ro and code not in rn:
                self.add("BREAKING" if str(code).startswith("2") else "RISKY", w, "response removed")
            elif code in rn and code not in ro:
                self.add("RISKY" if str(code).startswith("2") else "SAFE", w, "response added")
            else:
                self.content(self.resolve(self.old, ro[code]), self.resolve(self.new, rn[code]), w, "response")
        so, sn = self.sec(self.old, op_old), self.sec(self.new, op_new)
        if so != sn:
            if not so and sn:
                self.add("BREAKING", where + ".security", f"authentication now required: {sorted(map(sorted, sn))}")
            elif so and not sn:
                self.add("RISKY", where + ".security", "authentication removed")
            else:
                self.add("RISKY", where + ".security", f"security requirements changed: {sorted(map(sorted, so))} -> {sorted(map(sorted, sn))}")

    @staticmethod
    def sec(doc, op):
        s = op.get("security", doc.get("security", []))
        return {frozenset(r.keys()) for r in s if isinstance(r, dict)} - {frozenset()}

    def openapi(self):
        po, pn = self.old.get("paths", {}), self.new.get("paths", {})
        for path in sorted(set(po) | set(pn)):
            w = f"paths.{path}"
            if path in po and path not in pn:
                self.add("BREAKING", w, "path removed")
                continue
            if path in pn and path not in po:
                self.add("SAFE", w, "path added")
                continue
            for m in METHODS:
                a, b = po[path].get(m), pn[path].get(m)
                if a is not None and b is None:
                    self.add("BREAKING", f"{w}.{m}", "operation removed")
                elif b is not None and a is None:
                    self.add("SAFE", f"{w}.{m}", "operation added")
                elif a is not None and b is not None:
                    self.operation(po[path], pn[path], a, b, f"{w}.{m}")


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except OSError as e:
        raise ValueError(f"cannot read {path}: {e.strerror}")
    except json.JSONDecodeError as e:
        raise ValueError(f"{path} is not valid JSON ({e.msg} at line {e.lineno}); convert YAML to JSON first")
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: top level must be a JSON object")
    if "swagger" in doc and "openapi" not in doc:
        raise ValueError(f"{path}: Swagger 2 is not supported; convert to OpenAPI 3 or pass the schemas as JSON Schema")
    return doc


def main():
    argv = sys.argv[1:]
    mode = "both"
    if "--mode" in argv:
        i = argv.index("--mode")
        if i + 1 >= len(argv) or argv[i + 1] not in ("request", "response", "both"):
            print("error: --mode must be request, response or both", file=sys.stderr)
            return 2
        mode = argv[i + 1]
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    try:
        old, new = load(args[0]), load(args[1])
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    d = Diff(old, new)
    is_api = "paths" in old or "paths" in new or "openapi" in old or "openapi" in new
    if is_api:
        d.openapi()
    else:
        for m in (("request", "response") if mode == "both" else (mode,)):
            d.schema(old, new, "$", m)
        # one change judged in two directions: keep the strictest class per location and topic
        strict = {}
        for lvl, w, msg in d.found:
            k = (w, " ".join(msg.split(":")[0].split()[:3]))
            if k not in strict or ORDER[lvl] < ORDER[strict[k][0]]:
                strict[k] = (lvl, w, msg)
        d.found = list(strict.values())
        if mode == "both":  # a harmless note beside a real problem at the same location is only noise
            bad_at = {w for lvl, w, _ in d.found if lvl != "SAFE"}
            d.found = [x for x in d.found if x[0] != "SAFE" or x[1] not in bad_at]
    found = sorted(d.found, key=lambda x: (ORDER[x[0]], x[1]))
    counts = {k: sum(1 for x in found if x[0] == k) for k in ORDER}
    if "--json" in sys.argv:
        print(json.dumps({"counts": counts, "changes": [dict(level=l, where=w, note=m) for l, w, m in found]}, indent=1))
    else:
        for lvl in ORDER:
            rows = [x for x in found if x[0] == lvl]
            if rows:
                print(f"{lvl} ({len(rows)})")
                for _, w, m in rows:
                    print(f"  {w}: {m}")
                print()
        if not found:
            print("no differences found")
        print("summary:", counts)
    return 1 if counts["BREAKING"] else 0


if __name__ == "__main__":
    sys.exit(main())
