import json
from operator import itemgetter
from networkx.classes.digraph import DiGraph
import DotGraphCreator as dgc


def read_RO(path):
    with open(path) as file:
        ros = json.load(file)
        file.close()
    return ros


def update_graph_with_ROs(graph, ros):
    for ro in ros:
        id, trigger, operations = itemgetter("id", "trigger", "operations")(ro)
        operations = ro["operations"]
        for op in operations:
            type = op["type"]
            if type == "replace":
                replace_action(graph, id, trigger, op)
            elif type == "delete":
                # not sure what to do here
                print("deleting")
            else:
                print("Adding")


def replace_action(graph: DiGraph, idRO, trigger, operation):
    # assuming there is always only 1 parent
    existing_node = operation["existingNode"]
    parent_node = list(graph.predecessors(existing_node))[0]
    is_first_new_node = True
    for node in operation["newNodes"]:
        # taking node id and the rest of its attributes
        node_copy = {**node}
        new_node_id = node_copy["id"]
        del node_copy["id"]

        # adding it to the graph
        # Currently assuming the added nodes are all actionNode
        graph.add_node(
            new_node_id,
            type="action",
            is_original=False,
            idRO=idRO,
            trigger=trigger,
            **node_copy
        )

        # copying the edge data if any but only to the first new node
        edge_range = graph.get_edge_data(parent_node, existing_node)
        edge_range = edge_range[0] if edge_range else {}
        graph.add_edge(
            parent_node, new_node_id, **edge_range if is_first_new_node else {}
        )

        # wont copy edge attributes further
        is_first_new_node = False

        # updating the parent node so the next new node has the correct edge
        parent_node = new_node_id

    # need one last edge from the last added node to the same node 'Existing_node' is pointing too
    graph.add_edge(parent_node, list(graph.successors(existing_node))[0])