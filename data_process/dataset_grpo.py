import json

src="/dfs/data/BAH/data_crop_along_time_5/data_shuffle_test_sft.jsonl"
dst="/dfs/data/BAH/data_crop_along_time_5/data_shuffle_test_grpo.jsonl"

n=0
with open(src,'r') as f, open(dst,'w') as g:
    for line in f:
        if not line.strip():
            continue
        x=json.loads(line)

        msgs=x.get("messages", [])
        # 找到最后一个assistant作为标注
        sol=None
        for m in reversed(msgs):
            if m.get("role")=="assistant":
                sol=m.get("content")
                break

        # 保留user消息作为prompt
        user_msgs=[m for m in msgs if m.get("role")=="user"]
        if sol is None:
            # 没有标注就跳过
            continue

        y=dict(x)
        y["messages"]=user_msgs
        y["solution"]=sol

        g.write(json.dumps(y, ensure_ascii=False) + "\n")
        n+=1

print("written:", n, "->", dst)

