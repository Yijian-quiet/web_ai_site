"""
轻量级逆合成模板匹配器
用 RDKit 对本地的反应模板做匹配，替代 gu26 API 调用
"""
import json, os, re, random
from rdkit import Chem
from rdkit.Chem import AllChem, rdChemReactions

# 内置模板（SMARTS 格式，用常见逆合成反应）
# 格式: (name, reaction_smarts, template_smarts_retro)
BUILTIN_TEMPLATES = [
    ("Amide coupling", "[C:1](=[O:2])[OH]>>[C:1](=[O:2])[Cl]", "[C:1](=[O:2])[Cl]>>[C:1](=[O:2])[OH]"),
    ("Boc deprotection", "[N:1][C:2]([O:3])([O:4])C(C)(C)C>>[N:1]", "[N:1]>>[N:1][C:2]([O:3])([O:4])C(C)(C)C"),
    ("Aldol condensation", "[C:1](=O)[CH2:2]>>[C:1](=O)[C:2]=[CH2]", "[C:1](=O)[C:2]=[CH2]>>[C:1](=O)[CH2:2]"),
    ("Ester hydrolysis", "[C:1](=[O:2])[O:3][C:4]>>[C:1](=[O:2])[OH]", "[C:1](=[O:2])[OH]>>[C:1](=[O:2])[O:3][C:4]"),
    ("Nitrile reduction", "[C:1]#[N:2]>>[C:1][NH2:2]", "[C:1][NH2:2]>>[C:1]#[N:2]"),
    ("Nitro reduction", "[N+:1]([O-:2])=O>>[NH2:1]", "[NH2:1]>>[N+:1]([O-:2])=O"),
    ("Simple alkylation", "[C:1][OH]>>[C:1]O[C:2]", "[C:1]O[C:2]>>[C:1][OH]"),
    ("Ketone to alcohol", "[C:1](=O)[C:2]>>[C:1]([OH])[C:2]", "[C:1]([OH])[C:2]>>[C:1](=O)[C:2]"),
]

def load_templates(template_path=None):
    """加载模板"""
    templates = []
    if template_path and os.path.exists(template_path):
        with open(template_path) as f:
            data = json.load(f)
            for item in data:
                if "smarts" in item:
                    templates.append((item.get("name", "unknown"), item["smarts"]))
    else:
        for name, _, retro_smarts in BUILTIN_TEMPLATES:
            templates.append((name, retro_smarts))
    return templates


def apply_templates(mol, templates, topk=10):
    """用模板对分子做逆合成，返回前体列表"""
    candidates = []
    mol_smiles = Chem.MolToSmiles(mol) if isinstance(mol, Chem.Mol) else mol
    mol_obj = Chem.MolFromSmiles(mol_smiles) if isinstance(mol_smiles, str) else mol
    
    if mol_obj is None:
        return candidates
    
    for name, smarts in templates:
        try:
            rxn = AllChem.ReactionFromSmarts(smarts)
            if rxn is None:
                continue
            products = rxn.RunReactants((mol_obj,))
            for p in products:
                if p:
                    try:
                        p_smiles = Chem.MolToSmiles(p[0])
                        if p_smiles:
                            # 简单评分：用模板名做 hash
                            score = random.uniform(0.3, 0.9)  # 简化版用随机分数
                            candidates.append((p_smiles, score, name))
                    except:
                        pass
        except:
            continue
    
    # 去重 + 按评分排序
    seen = set()
    unique = []
    for smi, score, name in sorted(candidates, key=lambda x: -x[1]):
        if smi not in seen:
            seen.add(smi)
            unique.append((smi, score, name))
    
    return unique[:topk]


def is_building_block(smiles, building_blocks):
    """检查是否在建筑分子集中"""
    if not building_blocks:
        return False
    canon = Chem.MolToSmiles(Chem.MolFromSmiles(smiles)) if Chem.MolFromSmiles(smiles) else smiles
    return canon in building_blocks


if __name__ == "__main__":
    # 测试
    print("测试模板匹配器...")
    templates = load_templates()
    print(f"加载了 {len(templates)} 个模板")
    
    test_mols = ["CC(=O)Oc1ccccc1C(=O)O", "c1ccccc1O", "CC(=O)Nc1ccccc1"]
    for smi in test_mols:
        mol = Chem.MolFromSmiles(smi)
        if mol:
            results = apply_templates(mol, templates, topk=5)
            print(f"\n{smi} -> {len(results)} 个结果")
            for r_smi, score, name in results[:3]:
                print(f"  {r_smi[:40]:40s} score={score:.3f} ({name})")
