import json
from operator import itemgetter


def read_JSON(path):
    """
    Reads a JSON file and returns its content.

    Args:
        path (str): Path to the file.

    Returns:
        json: JSON object
    """
    with open(path) as file:
        obj = json.load(file)
        file.close()
    return obj


def update_graph_with_ROs(graph, ros):
    """
    Excutes the operations (replace, delete, add) of every revision operators.
    Args:
        graph (networkx graph): The graph.
        ros (list): List of JSON like object.
    """
    for ro in ros:
        id, trigger, operations = itemgetter("id", "trigger", "operations")(ro)
        operations = ro["operations"]
        for op in operations:
            type = op["type"]
            if type == "replace":
                replace_operation(graph, id, trigger, op)
            elif type == "delete":
                delete_operation(graph, op)
            else:
                add_action(graph, id, trigger, op)


def add_all_new_nodes(graph, id_ro, trigger, operation):
    """
    Add a list of new nodes with some attributes. These nodes do not have any edges after the execution of this function.

    Use 'add_all_new_edges' to add the respectives edges.

    Args:
        graph (networkx graph): The graph.
        id_ro (str): The ID of the revision operator.
        trigger (list): List of triggering nodes.
        operation (object): The operation object.
    """
    edge_to_successors = []
    for node in operation["newNodes"]:
        # taking node id and the rest of its attributes
        node_copy = {**node}
        new_node_id = node_copy["id"]
        node_type = node_copy["type"]

        # if the current node needs to connect to the successors of the 'existing node'
        if node_copy.get("edgeToSuccessors", False):
            edge_to_successors.append(
                {"node": new_node_id, **node_copy.get("edgeToSuccessorsAttr", {})}
            )

        if node_type == "action":
            node_copy["is_original"] = False

        node_copy.pop("id", None)
        node_copy.pop("type", None)
        node_copy.pop("predecessors", None)
        node_copy.pop("edgeToSuccessors", None)

        # adding it to the graph
        # Currently assuming the added nodes are all actionNode
        graph.add_node(
            new_node_id, type=node_type, idRO=id_ro, trigger=trigger, **node_copy
        )
    return edge_to_successors


def add_all_new_edges(graph, operation, edge_to_successors):
    """
    Add all the edges from the operation object.

    Nodes related to these edges must be added to the graph prior to this function call.

    Use 'add_all_new_nodes' to add the respectives nodes before calling this function.


    Args:
        graph (networkx graph): The graph.
        id_ro (str): The ID of the revision operator.
        trigger (list): List of triggering nodes.
        operation (object): The operation object.
    """
    existing_node = operation["existingNode"]

    for node in operation["newNodes"]:
        node_copy = {**node}
        new_node_id = node_copy["id"]

        predecessor_list = node_copy.get(
            "predecessors", list(graph.predecessors(existing_node))
        )

        for pred in predecessor_list:
            if isinstance(pred, str):
                pred = {"nodeId": pred}
            pred_node = pred["nodeId"]
            pred.pop("nodeId", None)
            # copying the edge data if any but only to the first new node
            edge_data = graph.get_edge_data(pred_node, existing_node)
            edge_data = edge_data[0] if edge_data else {}
            if not graph.has_edge(pred_node, new_node_id):
                graph.add_edge(pred_node, new_node_id, **pred, **edge_data)

            current_existing_nodes_successors = list(graph.successors(existing_node))

    for edge in edge_to_successors:
        node = edge["node"]
        edge.pop("node", None)
        for succ in current_existing_nodes_successors:
            if not graph.has_edge(node, succ):
                # need one last edge from the last added node to the same node 'Existing_node' is pointing too
                graph.add_edge(node, succ, **edge)


def replace_operation(graph, id_ro, trigger, operation):
    """
    Replace operation inserts a sequence of new nodes.

    This function is a 2-steps process. First, we add all the nodes to be added. Secondly, we add all the edges.

    This allows the RO file to have the nodes in any particular order.

    Args:
        graph (networkx graph): The graph.
        id_ro (str): The ID of the revision operator.
        trigger (list): List of triggering nodes.
        operation (object): The operation object
    """
    edge_to_successors = add_all_new_nodes(graph, id_ro, trigger, operation)
    add_all_new_edges(graph, operation, edge_to_successors)


def delete_operation(graph, operation):
    """
    Deletes a node. Links its predecessors and successors together.

    Args:
        graph (networkx graph): The graph.
        operation (str): The operation object
    """
    node_to_delete = operation["existingNode"]
    predecessors = graph.predecessors(node_to_delete)
    successors = graph.successors(node_to_delete)

    for pred in predecessors:
        for succ in successors:
            pred_edge_data = graph.get_edge_data(pred, node_to_delete)[0]
            succ_edge_data = graph.get_edge_data(node_to_delete, succ)[0]

            if not graph.has_edge(pred, succ):
                graph.add_edge(pred, succ, **pred_edge_data, **succ_edge_data)


def add_action(graph, idRO, trigger, operation):
    """
    Add operation inserts a node(s) between a list of predeccessors and successors.

    Args:
        graph (networkx graph): The graph.
        idRO (str): The ID of the revision operator.
        trigger (list): List of triggering nodes.
        operation (str): The operation object
    """
    predecessors = operation["predecessors"]
    successors = operation["successors"]

    addedNodes = operation["newNodes"]

    for predecessor in predecessors:
        for successor in successors:
            for node in addedNodes:
                # taking node id and the rest of its attributes
                node_copy = {**node}
                new_node_id = node_copy["id"]

                node_type = node_copy["type"]
                del node_copy["id"]
                del node_copy["type"]

                # Decision node attributes
                # node_dataItem = node_copy.get("dataItem", None)
                node_range = node_copy.get("range", None)
                # node_copy.pop("dataItem", None)
                node_copy.pop("range", None)

                # adding it to the graph
                # Currently assuming the added nodes are all actionNode

                graph.add_node(
                    new_node_id,
                    type=node_type,
                    is_original=False,
                    idRO=idRO,
                    trigger=trigger,
                    **node_copy
                )
                # print(graph.get_edge_data(predecessor, successor)[0])
                # nwx.add_path(graph,[predecessor, new_node_id, successor])

                # Case where the Predecessor node and successor node are adjecent
                if graph.has_edge(predecessor, successor):
                    # Adding the edge between the new node and the predecessor with the edge data
                    # We only want one edge between the predecessor and the new node
                    if not graph.has_edge(predecessor, new_node_id):
                        graph.add_edge(
                            predecessor,
                            new_node_id,
                            **graph.get_edge_data(predecessor, successor)[0]
                        )

                    # We need to remove the edges between the predecessor and the successor
                    graph.remove_edge(predecessor, successor)

                # Case where the predecessor node is not adjacent to the successor node
                else:
                    tmpSuccessors = list(graph.successors(predecessor))

                    for tmpSuccessor in tmpSuccessors:
                        # What range data do we want to copy/overlap?
                        # Using the first edge data for now
                        if graph.get_edge_data(predecessor, tmpSuccessor):
                            tmpData = graph.get_edge_data(predecessor, tmpSuccessor)[0]
                            # We only want one edge between the predecessor and the new node
                            if not graph.has_edge(predecessor, new_node_id):
                                graph.add_edge(predecessor, new_node_id, **tmpData)
                            break
                # print(graph.edges(new_node_id))
            # Adding the edge between the new node and the successor with the edge data

            # We only want one edge between the new node and the successor
            if not graph.has_edge(new_node_id, successor):
                if node_type == "decision":
                    for ranges in node_range:
                        if ranges.get("successors", None) == successor:
                            graph.add_edge(
                                new_node_id, successor, range=ranges.get("value", None)
                            )
                else:
                    graph.add_edge(new_node_id, successor)
