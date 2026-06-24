"""
MCTS Policy & Value 函数 — 通过 gu26 单步 API 调用，替代 ChemBart 模型
"""
import json
import requests
import numpy as np
from .mcts_base import NODE
from .utils import utils

API_BASE = "http://localhost:8001"
SINGLE_STEP_URL = f"{API_BASE}/retroplanner/api/single_step"

DEFAULT_MODEL = "Reaxys"
DEFAULT_TOPK = 10
REQUEST_TIMEOUT = 120


def _call_single_step_api(smiles, model=DEFAULT_MODEL, topk=DEFAULT_TOPK):
    """调用 gu26 单步 API 获取前体候选"""
    payload = {
        "smiles": smiles,
        "savedOptions": {
            "topk": topk,
            "oneStepModel": [model]
        }
    }
    try:
        resp = requests.post(SINGLE_STEP_URL, json=payload, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return None
        return resp.json()
    except:
        return None


def _parse_single_step_result(api_result):
    """解析单步 API 返回"""
    if api_result is None or api_result.get("status") != "success":
        return []
    one_step = api_result.get("one_step_results", {})
    if not one_step:
        return []
    reactants = one_step.get("reactants", [])
    scores = one_step.get("scores", [])
    if not reactants:
        return []
    while len(scores) < len(reactants):
        scores.append(0.0)
    return list(zip(reactants, scores))


def _normalize(probs):
    total = sum(probs)
    return [p / total for p in probs] if total > 0 else probs


def GenChildnodePolicy(smi, model=DEFAULT_MODEL, topk=DEFAULT_TOPK):
    """策略函数：生成子节点（候选前体）及概率分布"""
    api_result = _call_single_step_api(smi, model=model, topk=topk)
    raw_candidates = _parse_single_step_result(api_result)
    if not raw_candidates:
        return NODE(childlist=[], reagent=[], Plist=[], V=None)

    # 去重、规范化
    state_dict = {}
    for precursor_smi, score in raw_candidates:
        precursor = utils.canonize(precursor_smi)
        if precursor is None or utils.weak_compare(precursor, smi):
            continue
        if precursor in state_dict:
            state_dict[precursor] += float(score)
        else:
            state_dict[precursor] = float(score)

    if not state_dict:
        return NODE(childlist=[], reagent=[], Plist=[], V=None)

    childlist = []
    Plist = []
    for precursor, score in state_dict.items():
        childlist.append(precursor.split("."))
        Plist.append(score)

    Plist = _normalize(Plist)
    return NODE(childlist=childlist, reagent=[None]*len(childlist), Plist=Plist, V=None)


def _mol_complexity(mol):
    """估算分子复杂度（重原子数 + 环数 + 立体中心数）"""
    if mol is None:
        return 100
    from rdkit import Chem
    num_atoms = mol.GetNumAtoms(onlyHeavy=True)
    num_rings = len(Chem.GetSSSR(mol))
    num_stereo = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
    return num_atoms + num_rings * 2 + num_stereo


def Value(smi, model=DEFAULT_MODEL, topk=10):
    """价值函数：结合模板置信度和分子复杂度"""
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return -1.0

    # 如果已经是基本分子，价值最高
    heavy = mol.GetNumAtoms(onlyHeavy=True)
    if heavy <= 3:
        return 2.0

    api_result = _call_single_step_api(smi, model=model, topk=topk)
    raw = _parse_single_step_result(api_result)
    if not raw:
        return -0.5

    # 置信度分数
    max_score = max(float(s) for _, s in raw)

    # 复杂度惩罚：复杂分子更难合成
    complexity = _mol_complexity(mol)
    penalty = max(0, (complexity - 10) * 0.05)

    # 价值 = 置信度信号 - 复杂度惩罚
    value = -np.log(1.0 - max_score + 1e-6) - penalty
    return float(max(value, -1.0))


def is_end(smi, basic_mol_set=None):
    """判断分子是否为末端（可买分子或极简单分子）"""
    if basic_mol_set and smi in basic_mol_set:
        return True
    # C<=3 且原子总数<=8 的极简单分子
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return False
    c_count = sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() == 6)
    heavy = mol.GetNumAtoms(onlyHeavy=True)
    return c_count <= 3 and heavy <= 8
