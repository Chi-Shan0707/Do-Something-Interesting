import pandas as pd

def load_subway_data(file_name):
    df = pd.read_csv(file_name)
    station_info = {}
    graph = {}
    # 遍历每行提取基础信息和换乘关系
    for index, row in df.iterrows():
        sid = int(row['站点ID'])
        line = row['线路名']
        name = row['站名']
        trans_ids_raw = row['可换乘站点ID']

        station_info[sid] = {'line': line, 'name': name}
        graph[sid] = []
        # 处理换乘 ID
        if pd.notna(trans_ids_raw):
            trans_ids = str(trans_ids_raw).split('/')
            for tid in trans_ids:
                if tid.strip():
                    graph[sid].append(int(tid))
    # 处理相邻站点
    last_id = None
    last_line = None
    for index, row in df.iterrows():
        curr_id = int(row['站点ID'])
        curr_line = row['线路名']
        # 如果当前站点与上一个站点属于同一线路，则它们在物理上相邻
        if last_line == curr_line:
            graph[curr_id].append(last_id)
            graph[last_id].append(curr_id)

        last_id = curr_id
        last_line = curr_line

    return station_info, graph

def find_path(curr_id, target_line, target_name, station_info, graph, visited):
    curr_info = station_info[curr_id]

    if curr_info['line'] == target_line and curr_info['name'] == target_name:
        return [curr_id]

    current_visited = visited + [curr_id]

    for neighbor in graph[curr_id]:
        if neighbor not in visited:

            result = find_path(neighbor, target_line, target_name, station_info, graph, current_visited)
            if result:
                return [curr_id] + result
    return None

def main():
    try:
        station_info, graph = load_subway_data('线路.csv')

        user_input = input("请输入起始和目的站点 (例: 18号线，复旦大学-10号线，交通大学): ")

        start_part, end_part = user_input.split('-')
        s_line, s_name = start_part.strip().split('，')
        e_line, e_name = end_part.strip().split('，')

        start_id = None
        for sid, info in station_info.items():
            if info['line'] == s_line and info['name'] == s_name:
                start_id = sid
                break

        if start_id is None:
            print("未找到起点，请检查线路名和站名是否正确。")
            return

        path = find_path(start_id, e_line, e_name, station_info, graph, [])

        if path:
            last_line = None
            for sid in path:
                info = station_info[sid]
                if last_line is not None and info['line'] != last_line:
                    print("换乘")

                print(f"{info['line']}，{info['name']}")
                last_line = info['line']
        else:
            print("未找到可用路径。")

    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()