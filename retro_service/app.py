"""轻量逆合成 API 服务"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
import base64, io

app = Flask(__name__)

# 加载模板匹配器
from template_matcher_v2 import Matcher as TMatcher, plan as do_plan
MATCHER = TMatcher('/var/www/web_ai/retro_service/templates/pistachio_5000.json')

# 加载建筑分子集
BASIC_MOL_PATH = os.path.join(os.path.dirname(__file__), "basic_mol.json")
BUILDING_BLOCKS = set()
if os.path.exists(BASIC_MOL_PATH):
    with open(BASIC_MOL_PATH) as f:
        BUILDING_BLOCKS = set(json.load(f))

# 预计算示例
DEMO_EXAMPLES = {
    "mol_new": {"smiles": "Cc1ccc(C(=O)N2CCN(CC2)C(=O)C3CCC(=O)N3)cc1", "name": "新颖分子"},
    "paroxetine": {"smiles": "C1CNCC1C2=CC=C(C=C2)OC3=CC=C(C=C3)F", "name": "帕罗西汀 (Paroxetine)"},
    "atorvastatin": {"smiles": "CC(C)C(=O)NC1=CC=C(C=C1)C2=CC=CC=C2", "name": "阿托伐他汀中间体"},
}


@app.route("/retro/api/health")
def health():
    return jsonify({"status": "ok", "templates": len(MATCHER.templates), "building_blocks": len(BUILDING_BLOCKS)})


@app.route("/retro/api/demo_examples")
def demo_examples():
    return jsonify(DEMO_EXAMPLES)


@app.route("/retro/api/render_svg", methods=["POST", "GET"])
def render_svg():
    data = request.get_json() if request.method == "POST" else request.args
    smiles = data.get("smiles", "")
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return jsonify({"error": "Invalid SMILES"}), 400
    try:
        svg = Draw.MolsToGridImage([mol], molsPerRow=1, subImgSize=(250, 150), useSVG=True)
        return jsonify({"svg": svg.split(chr(62)+chr(10), 1)[-1] if svg.startswith(chr(60)+chr(63)+chr(120)+chr(109)+chr(108)) else svg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/retro/api/plan", methods=["POST"])
def plan():
    data = request.get_json()
    smiles = data.get("smiles", "")
    max_depth = data.get("max_steps", 5)
    
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return jsonify({"success": False, "error": "Invalid SMILES"}), 400
    
    result = do_plan(smiles, MATCHER, set() if smiles in BUILDING_BLOCKS else BUILDING_BLOCKS, max_depth=max_depth, topk=5)
    
    routes_json = []
    for route in result["routes"]:
        routes_json.append({
            "path": route["path"],
            "status": route["status"],
            "template": route.get("template", ""),
            "score": route.get("score", 0)
        })
    

@app.route("/retro/api/mol_svg")
def mol_svg():
    smiles = request.args.get("s", "")
    if not smiles:
        return "", 400
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return "", 404
    try:
        from rdkit.Chem import rdDepictor
        from rdkit.Chem.Draw import rdMolDraw2D
        mc = Chem.Mol(mol.ToBinary())
        if not mc.GetNumConformers():
            rdDepictor.Compute2DCoords(mc)
        drawer = rdMolDraw2D.MolDraw2DSVG(200, 150)
        opts = drawer.drawOptions()
        opts.backgroundColour = (1.0, 1.0, 1.0, 0.0)
        drawer.DrawMolecule(mc)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        if "xmlns" not in svg:
            svg = svg.replace("<svg ", "<svg xmlns=\"http://www.w3.org/2000/svg\" ")
        return svg, 200, {"Content-Type": "image/svg+xml", "Access-Control-Allow-Origin": "*"}
    except Exception as e:
        return str(e), 500

@app.route("/retro/api/mol_png")
def mol_png():
    smiles = request.args.get("s", "")
    if not smiles:
        return "", 400
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return "", 404
    try:
        img = Draw.MolsToGridImage([mol], molsPerRow=1, subImgSize=(200, 150))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue(), 200, {"Content-Type": "image/png"}
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, threaded=True)
