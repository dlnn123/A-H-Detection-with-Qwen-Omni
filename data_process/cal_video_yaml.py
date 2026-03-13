import yaml
import os
import sys
from collections import defaultdict

# 自定义构造器：处理Python tuple标签
def tuple_constructor(loader, node):
    return list(loader.construct_sequence(node))
yaml.add_constructor('tag:yaml.org,2002:python/tuple', tuple_constructor)

def check_yaml_null_fields(yaml_file_path, target_fields=None):
    if target_fields is None:
        # target_fields = ['audio', 'body', 'facial', 'inconsistencies', 'language']
        target_fields = ['audio', 'body', 'facial', 'inconsistencies']
    # 基础统计变量
    total_entries = 0          
    all_null_entries = 0       
    partial_null_entries = 0   
    null_entry_details = []    
    partial_null_details = []  # 部分null条目详情（前10条）
    
    # 新增：统计部分null条目中各字段的非null次数
    field_non_null_count = defaultdict(int)
    # 新增：统计部分null条目中各字段的非null占比
    field_non_null_ratio = {}

    if not os.path.exists(yaml_file_path):
        print(f"错误：文件 {yaml_file_path} 不存在！")
        return None

    try:
        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f, Loader=yaml.Loader)
        
        def traverse_data(data, parent_path="root"):
            nonlocal total_entries, all_null_entries, partial_null_entries
            
            if isinstance(data, dict):
                # has_target_field = any(field in data for field in target_fields)
                has_target_field = all(field in data for field in target_fields)
                if has_target_field:
                    total_entries += 1
                    field_values = {field: data.get(field) for field in target_fields}
                    is_all_null = all(v is None for v in field_values.values())
                    
                    if is_all_null:
                        all_null_entries += 1
                        if len(null_entry_details) < 10:  # 只存前10条
                            null_entry_details.append({
                                'path': parent_path,
                                'field_values': field_values
                            })
                    else:
                        partial_null_entries += 1
                        # 1. 统计各字段非null次数
                        for field, value in field_values.items():
                            if value is not None:
                                field_non_null_count[field] += 1
                        # 2. 保存前10条部分null条目详情
                        if len(partial_null_details) < 10:
                            partial_null_details.append({
                                'path': parent_path,
                                'field_values': field_values
                            })
            
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    traverse_data(item, f"{parent_path}[{idx}]")
            elif isinstance(data, dict):
                for key, value in data.items():
                    traverse_data(value, f"{parent_path}.{key}")

        traverse_data(data)

        # 计算基础占比
        all_null_ratio = (all_null_entries / total_entries) * 100 if total_entries > 0 else 0
        partial_null_ratio = (partial_null_entries / total_entries) * 100 if total_entries > 0 else 0
        
        # 计算各字段在部分null条目中的非null占比
        if partial_null_entries > 0:
            for field in target_fields:
                field_non_null_ratio[field] = round(
                    (field_non_null_count[field] / partial_null_entries) * 100, 
                    2
                )
        else:
            for field in target_fields:
                field_non_null_ratio[field] = 0.0

        result = {
            '文件路径': yaml_file_path,
            '目标检查字段': target_fields,
            '包含目标字段的条目总数': total_entries,
            '所有字段都为null的条目数': all_null_entries,
            '部分字段为null的条目数': partial_null_entries,
            '全null条目占比(%)': round(all_null_ratio, 2),
            '部分null条目占比(%)': round(partial_null_ratio, 2),
            '全null条目详情': null_entry_details,
            '部分null条目详情': partial_null_details,
            '部分null条目-各字段非null次数': dict(field_non_null_count),
            '部分null条目-各字段非null占比(%)': field_non_null_ratio
        }

        return result

    except yaml.YAMLError as e:
        print(f"YAML解析错误：{str(e)}")
        print(f"错误位置：行 {e.mark.line + 1}，列 {e.mark.column + 1}")
        return None
    except Exception as e:
        print(f"程序执行错误：{str(e)}")
        return None

# 示例调用
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法：python cal_video_yaml.py <YAML文件路径>")
        print("示例：python cal_video_yaml.py /dfs/data/BAH/video_annotation_transcript.yaml")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    stats = check_yaml_null_fields(yaml_file)
    
    if stats:
        # 1. 基础统计结果
        print("\n===== YAML字段null统计结果 ======")
        print(f"📁 文件路径：{stats['文件路径']}")
        print(f"🔍 检查字段：{', '.join(stats['目标检查字段'])}")
        print(f"📊 包含目标字段的条目总数：{stats['包含目标字段的条目总数']}")
        print("├─ 所有字段都为null：")
        print(f"│  ├─ 条目数：{stats['所有字段都为null的条目数']}")
        print(f"│  └─ 占比：{stats['全null条目占比(%)']}%")
        print("└─ 部分字段为null：")
        print(f"   ├─ 条目数：{stats['部分字段为null的条目数']}")
        print(f"   └─ 占比：{stats['部分null条目占比(%)']}%")

        # 2. 部分null条目-各字段非null占比分析（核心新增）
        print("\n===== 部分null条目-字段非null占比排行 =====")
        # 按非null占比降序排序
        sorted_fields = sorted(
            stats['部分null条目-各字段非null占比(%)'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for idx, (field, ratio) in enumerate(sorted_fields, 1):
            count = stats['部分null条目-各字段非null次数'].get(field, 0)
            print(f"{idx}. {field}：非null次数={count}，占比={ratio}%")

        # 3. 前10条全null条目详情
        if stats['全null条目详情']:
            print(f"\n===== 前{len(stats['全null条目详情'])}条全null条目详情 =====")
            for idx, detail in enumerate(stats['全null条目详情']):
                print(f"  条目{idx+1} - 路径：{detail['path']} | 字段值：{detail['field_values']}")
        
        # 4. 前10条部分null条目详情（核心新增）
        if stats['部分null条目详情']:
            print(f"\n===== 前{len(stats['部分null条目详情'])}条部分null条目详情 =====")
            for idx, detail in enumerate(stats['部分null条目详情']):
                print(f"  条目{idx+1} - 路径：{detail['path']} | 字段值：{detail['field_values']}")