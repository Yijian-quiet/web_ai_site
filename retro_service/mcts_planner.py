"""
MCTS Planner Demo — 使用 gu26 单步 API，替换 ChemBart 模型
"""
import os, sys, json
from pathlib import Path

# Add mcts_core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcts_core.mcts_base import MCTS_BASE, ROUTE
from mcts_core.policy_value_api import GenChildnodePolicy, Value, is_end
from mcts_core.utils import utils


class MY_MCTS(MCTS_BASE):
    """MCTS 子类：整合策略网络和价值函数"""
    def __init__(self, basic_mol_path=None, model="Reaxys", topk=20, **params):
        # 加载基本分子集（可买分子库）
        self.end_set = set()
        if basic_mol_path and os.path.exists(basic_mol_path):
            with open(basic_mol_path) as f:
                self.end_set = set(json.load(f))
        
        self.model = model
        self.topk = topk
        super().__init__(
            gen_choice=self.gen_choice,
            is_end=self.is_end_check,
            gen_value=self.gen_value,
            **params
        )
    
    def gen_choice(self, status):
        """生成策略：调用单步 API"""
        return GenChildnodePolicy(status, model=self.model, topk=self.topk)
    
    def gen_value(self, status):
        """价值评估"""
        return Value(status, model=self.model, topk=self.topk)
    
    def is_end_check(self, status):
        """末端判断"""
        return is_end(status, self.end_set)


def plan_molecule(target_smiles, model="Reaxys", topk=20,
                  mcts_times=50, max_route_len=8, max_search_depth=8,
                  Cpuct=1.0, alternatives=1,
                  basic_mol_path=None, save_path=None):
    """
    单分子 MCTS 规划入口
    返回: { "answer_0_..._route_0": [...], ... }
    """
    # 规范化
    root = utils.canonize(target_smiles)
    if root is None:
        return {"error": "Invalid SMILES"}
    
    # 检查是否已在基本分子集中
    if is_end(root, set(json.load(open(basic_mol_path))) if basic_mol_path and os.path.exists(basic_mol_path) else None):
        return {"answer_0_" + root + "_route_0": [
            {"success": 1, "probability": 1.0},
            {root: "basic mol"},
            {root: "basic mol"}
        ]}
    
    # 创建 MCTS 实例
    mcts = MY_MCTS(
        basic_mol_path=basic_mol_path,
        model=model,
        topk=topk,
        mcts_times=mcts_times,
        max_route_len=max_route_len,
        max_search_depth=max_search_depth,
        Cpuct=Cpuct,
        update_method='avg',
        debug=False
    )
    
    # 执行搜索
    result = mcts.play(
        root=root,
        idx=0,
        file_path=save_path or '/tmp/mcts_demo',
        alternatives=alternatives,
        train=False
    )
    
    return result


if __name__ == '__main__':
    # 测试
    import time
    
    test_mols = [
        ("COc1ccc(C(C)=O)cc1", 5),  # 简单酚酮类
        ("c1ccccc1", 3),             # 苯
    ]
    
    for smi, alt in test_mols:
        print(f"\n{'='*60}")
        print(f"规划目标: {smi} (alternatives={alt})")
        print(f"{'='*60}")
        t0 = time.time()
        
        result = plan_molecule(
            target_smiles=smi,
            model="Reaxys",
            topk=10,
            mcts_times=30,
            max_route_len=5,
            max_search_depth=5,
            Cpuct=5.0,
            alternatives=alt,
            basic_mol_path=None
        )
        
        elapsed = time.time() - t0
        print(f"耗时: {elapsed:.1f}s")
        
        for route_name, route_data in result.items():
            print(f"\n{route_name}:")
            print(f"  success: {route_data[0]}")
            print(f"  route_tree: {json.dumps(route_data[1], indent=2)[:500]}")
        
        print()
