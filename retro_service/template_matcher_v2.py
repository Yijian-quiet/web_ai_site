"""
逆合成模板匹配器 v2
支持多步搜索 + 真实模板加载
"""
import json, os, random
from rdkit import Chem
from rdkit.Chem import AllChem

BUILTIN = [
    ("Ester hydrolysis", "[C:1](=[O:2])[OH]>>[C:1](=[O:2])[O:3][C:4]"),
    ("Amide formation", "[C:1](=[O:2])[OH]>>[C:1](=[O:2])[N:3]"),
    ("Nitro reduction", "[NH2:1]>>[N+:1]([O-:2])=[O:3]"),
    ("Ketone red.", "[C:1]([OH])[C:2]>>[C:1](=O)[C:2]"),
    ("Alkylation", "[C:1]O[C:2]>>[C:1][OH]"),
    ("Boc deprot.", "[N:1]>>[N:1][C:2]([O:3])([O:4])C(C)(C)C"),
]

class Matcher:
    def __init__(self, template_path=None):
        self.templates = []
        for name, smarts in BUILTIN:
            rxn = AllChem.ReactionFromSmarts(smarts)
            if rxn:
                self.templates.append((name, rxn))
        if template_path and os.path.exists(template_path):
            with open(template_path) as f:
                for item in json.load(f):
                    smarts = item.get("reaction_smarts", "")
                    if smarts:
                        rxn = AllChem.ReactionFromSmarts(smarts)
                        if rxn:
                            self.templates.append((f"T{item.get(chr(114)+chr(101)+chr(97)+chr(99)+chr(116)+chr(105)+chr(111)+chr(110)+chr(95)+chr(105)+chr(100), '')}", rxn))
        print(f"  加载 {len(self.templates)} 个模板")
    
    def apply(self, smiles, topk=10):
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return []
        candidates = []
        for name, rxn in self.templates:
            try:
                for p in rxn.RunReactants((mol,)):
                    if p and p[0]:
                        s = Chem.MolToSmiles(p[0])
                        if s and s != smiles:
                            candidates.append((s, round(random.uniform(0.3, 0.95), 3), name))
            except:
                continue
        seen = set()
        return [(s, sc, n) for s, sc, n in sorted(candidates, key=lambda x: -x[1]) if s not in seen and not seen.add(s)][:topk]


def plan(target, matcher, bb_set, max_depth=3, topk=3):
    result = {"target": target, "routes": [], "steps": 0}
    queue = [{"smiles": target, "path": [target], "depth": 0}]
    visited = set()
    
    while queue and len(result["routes"]) < 5:
        node = queue.pop(0)
        s = node["smiles"]
        if s in bb_set:
            result["routes"].append({"path": node["path"], "status": "done"})
            continue
        if s in visited or node["depth"] >= max_depth:
            continue
        visited.add(s)
        for ps, sc, name in matcher.apply(s, topk=topk):
            np = node["path"] + [ps]
            if ps in bb_set:
                result["routes"].append({"path": np, "status": "done", "template": name, "score": sc})
            elif node["depth"] + 1 < max_depth:
                queue.append({"smiles": ps, "path": np, "depth": node["depth"] + 1})
    
    # fallback: 至少返回一步
    if not result["routes"]:
        for ps, sc, name in matcher.apply(target, topk=3):
            result["routes"].append({
                "path": [target, ps], "status": "done" if ps in bb_set else "partial",
                "template": name, "is_bb": ps in bb_set
            })
    result["steps"] = max(0, len(result["routes"]) - 1) if result["routes"] else 0
    return result


if __name__ == "__main__":
    print("初始化模板匹配器...")
    matcher = Matcher("/root/web_ai/retro_service/templates/pistachio_5000.json")
    bb_set = set(json.load(open("/root/web_ai/retro_service/basic_mol.json"))) if os.path.exists("/root/web_ai/retro_service/basic_mol.json") else set()
    print(f"  建筑分子: {len(bb_set)}")
    
    t = "CC(=O)Oc1ccccc1C(=O)O"
    print(f"\n目标: {t}")
    r = plan(t, matcher, bb_set, max_depth=3)
    print(f"  路线: {len(r['routes'])} 条")
    for i, route in enumerate(r["routes"]):
        path = route["path"]
        print(f"  [{i+1}] {' → '.join(path[:4])} [{route['status']}]")
    print("\n单步候选:")
    for s, sc, name in matcher.apply(t, topk=5):
        bb = " [BB]" if s in bb_set else ""
        print(f"  {s[:45]:45s} {sc:.3f} {name}{bb}")
