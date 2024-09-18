import pandas as pd
import networkx as nx
from pyvis.network import Network


COLORS = [
    "#FF6F61",  # (Coral)
    "#FF8C42",  # (Vivid Orange)
    "#7a7aff",  # (Royal Blue)
    "#FFD700",  # (Golden Yellow)
    "#40E0D0",  # (Turquoise)
    "#FF69B4",  # (Hot Pink)
    "#FF6347",  # (Tomato)
    "#FFA500",  # (Orange)
    "#FFD700",  # (Gold)
    "#32CD32",  # (Lime Green)
    "#4682B4",  # (Steel Blue)
    "#FF1493",  # (Deep Pink)
    "#FFA07A",  # (Light Salmon)
    "#FF8C00",  # (Dark Orange)
    "#8FBC8F",  # (Dark Sea Green)
    "#00CED1",  # (Dark Turquoise)
    "#FF4500",  # (Orange Red)
    "#DB7093",  # (Pale Violet Red)
    "#9ACD32",  # (Yellow Green)
    "#FF00FF",  # (Magenta)
    "#FF6347",  # (Tomato Red)
    "#C71585",  # (Medium Violet Red)
]


def main() -> None:
    base_path = "ragtest/output/20240916-111521/artifacts/"
    df_en = pd.read_parquet(base_path + "create_final_entities.parquet")
    df = pd.read_parquet(base_path + "create_final_relationships.parquet")

    G = nx.from_pandas_edgelist(df[["source", "target"]])
    temp = []
    for i, j in zip(df_en["type"].unique().tolist(), COLORS):
        temp_dict = {}
        temp_dict["type"] = i
        temp_dict["color"] = j
        temp.append(temp_dict)

    edges = []
    for _, row in df.iterrows():
        edges.append((row["source"], row["target"]))

    nodes = list(G.nodes())
    node_list = []
    for _node in nodes:
        _type = df_en.loc[df_en["name"] == _node, "type"].values[0]
        node_dict = {}
        node_dict["node"] = _node
        node_dict["type"] = _type
        for _temp in temp:
            if _temp["type"] == _type:
                node_dict["color"] = _temp["color"]
        node_list.append(node_dict)

    net2 = Network(height="900px")
    for _node in node_list:
        net2.add_node(_node["node"], label=_node["node"], color=_node["color"])
    net2.add_edges(edges)
    net2.show_buttons(filter_=["physics"])
    net2.show("attack_on_graph.html", notebook=False)


if __name__ == "__main__":
    main()
