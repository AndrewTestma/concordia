from PlayerState import PlayerState
import logging

# 配置日志以便看到 PlayerState 的输出
logging.basicConfig(level=logging.INFO)

def test_player_state():
    print("--- 开始测试 PlayerState ---")

    # 1. 初始化
    p1 = PlayerState("p1", "Alice", "Villager")
    all_players = ["p1", "p2", "p3", "p4"]

    # 2. 测试怀疑矩阵初始化
    p1.init_suspicion(all_players)
    print(f"初始怀疑矩阵: {p1.suspicion_matrix}")
    assert len(p1.suspicion_matrix) == 3
    assert p1.get_suspicion("p2") == 50.0

    # 3. 测试更新怀疑度
    p1.update_suspicion("p2", 20, "行为可疑")
    print(f"更新后 p2 怀疑度: {p1.get_suspicion('p2')}")
    assert p1.get_suspicion("p2") == 70.0

    p1.update_suspicion("p3", -10, "有好人面")
    print(f"更新后 p3 怀疑度: {p1.get_suspicion('p3')}")
    assert p1.get_suspicion("p3") == 40.0

    # 测试边界
    p1.update_suspicion("p2", 100, "查杀")
    print(f"边界测试 p2 (max 100): {p1.get_suspicion('p2')}")
    assert p1.get_suspicion("p2") == 100.0

    # 4. 测试获取最怀疑的人
    most_suspicious = p1.get_most_suspicious(1)
    print(f"最怀疑的人: {most_suspicious}")
    assert most_suspicious[0][0] == "p2"

    # 5. 测试待办问题
    p1.add_question("p3 是谁?")
    p1.add_question("p4 为什么投票给 p1?")

    questions = p1.get_all_questions()
    print(f"当前问题: {questions}")
    assert len(questions) == 2

    q1 = p1.pop_question()
    print(f"取出一个问题: {q1}")
    assert q1 == "p3 是谁?"
    assert len(p1.get_all_questions()) == 1

    print("--- PlayerState 测试通过 ---")

if __name__ == "__main__":
    test_player_state()
