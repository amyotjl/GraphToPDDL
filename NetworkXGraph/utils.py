import networkx as nwx


def get_type_nodes(graph, node_type):
    """
    Retrieves list of nodes of the given type

    Args:
        graph (networkx graph): The graph.
        node_type (str): Type of the nodes to retrieve.

    Returns:
        list: List of node of the given type.

    """
    return [node for node, attr in graph.nodes.items() if attr["type"] == node_type]


def find_goal_node(graph, start_node):
    """
    Finds a goal node recursively from a given start_node.

    Goal node MUST NOT have any out edges.

    Args:
        graph (networkx graph): The graph.
        start_node (str): Node to start the search.

    Returns:
        str: Name of the goal node.

    """
    out_edges = graph.out_edges(start_node)
    if len(out_edges):
        return find_goal_node(graph, list(out_edges)[0][1])
    return start_node


def find_init_node(graph, start_node):
    """
    Finds a initial node recursively from a given start_node.

    Initial node MUST NOT have any in edges.

    Args:
        graph (networkx graph): The graph.
        start_node (str): Node to start the search.

    Returns:
        str: Name of the goal node.

    """
    in_edges = graph.in_edges(start_node)
    if len(in_edges):
        return find_init_node(graph, list(in_edges)[0][0])
    return start_node


def get_metric_name(metric):
    """
    Extract the name of the metric.

    Metrics are node attributs that contains the word 'Cost'.

    Args:
        metric (str): The metric.

    Returns:
        str: Name of the metric.

    """
    metric_name = metric if metric == "cost" else metric.replace("Cost", "")
    return metric_name


def get_all_parallel_nodes(graph):
    """
    Finds all the nodes involved in parallel paths.

    Args:
        graph (networkx graph): The graph.


    Returns:
        list: List of parallel nodes.

    """
    parallel_nodes = []
    for node, attributes in graph.nodes.items():

        if attributes.get("is_in_parallel") == True:
            parallel_nodes.append(f"{node}")

    return parallel_nodes


def find_parallel_path(graph, p_nodes_found):
    parallelNode = ""
    # TODO: numParallelPaths for each diseases

    for start_node in p_nodes_found:
        for end_node in p_nodes_found:

            parallel_sequence = list(
                nwx.all_simple_paths(graph, source=start_node, target=end_node)
            )
            if not parallel_sequence:
                continue
            elif len(parallel_sequence) == 1:
                continue
            else:
                parallelTypeNode = ""
                untraversedParallelNode = ""

                parallelNode += "(parallelStartNode {})\n\t".format(start_node)
                parallelNode += "(parallelEndNode {})\n\t".format(end_node)

                # for path in parallel_sequence:
                (
                    parallelTypeNode,
                    untraversedParallelNode,
                ) = update_between_parallel_nodes(
                    graph,
                    start_node,
                    end_node,
                    parallelTypeNode,
                    untraversedParallelNode,
                )

                parallelNode += parallelTypeNode
                parallelNode += untraversedParallelNode

    return parallelNode


def update_between_parallel_nodes(
    graph,
    start_node,
    end_node,
    parallelTypeNode,
    untraversedParallelNode,
    numParallelPaths=0,
):
    if start_node == end_node:
        return parallelTypeNode, untraversedParallelNode

    if type(start_node) == str:
        first_path, *path_list = graph.out_edges(start_node)
    else:
        first_path, *path_list = start_node

    if len(path_list) == 1:
        _, node = path_list.pop()
        _, nodefp = first_path
        parallelTypeNode, untraversedParallelNode = update_between_parallel_nodes(
            graph,
            nodefp,
            end_node,
            parallelTypeNode,
            untraversedParallelNode,
            numParallelPaths + 1,
        )
        return update_between_parallel_nodes(
            graph,
            node,
            end_node,
            parallelTypeNode,
            untraversedParallelNode,
            numParallelPaths + 1,
        )

    elif len(path_list) > 1:
        _, nodefp = first_path
        parallelTypeNode, untraversedParallelNode = update_between_parallel_nodes(
            graph,
            nodefp,
            end_node,
            parallelTypeNode,
            untraversedParallelNode,
            numParallelPaths + 1,
        )

        return update_between_parallel_nodes(
            graph,
            path_list,
            end_node,
            parallelTypeNode,
            untraversedParallelNode,
            numParallelPaths + 1,
        )

    if graph.nodes[start_node]["type"] != "parallel":
        graph.nodes[start_node]["is_in_parallel"] = True

        parallelTypeNode += "(parallel{}Node {})\n\t".format(
            graph.nodes[start_node]["type"].capitalize(), start_node
        )
        untraversedParallelNode += "(untraversedParallelNode p{})\n\t".format(
            start_node
        )

    _, node = first_path
    return update_between_parallel_nodes(
        graph,
        node,
        end_node,
        parallelTypeNode,
        untraversedParallelNode,
        numParallelPaths + 1,
    )


def get_all_metrics(graph):
    """
    Finds all the metrics.

    Metrics are node attributs that contains the word 'Cost'.

    Args:
        graph (networkx graph): The graph.


    Returns:
        list: List of metrics.

    """
    action_nodes = get_type_nodes(graph, "action")
    metrics = []
    for node in action_nodes:
        node_metrics = [
            attr for attr in graph.nodes[node] if attr.lower().find("cost") != -1
        ]
        metrics.extend(node_metrics)
    return list(set(metrics))


def get_all_revIds(graph):
    """
    Finds all revision IDs.

    Args:
        graph (networkx graph): The graph.

    Returns:
        list: List of revision IDs.
    """
    revIds = []
    for _, attr in graph.nodes.items():
        idRO = attr.get("idRO", False)
        if idRO and idRO not in revIds:
            revIds.append(idRO)
    return revIds


def find_revId_involved_nodes(graph, revId):
    """
    Finds all the nodes involved in a given revision ID. This includes the list of triggering nodes and the inserted nodes

    Args:
        graph (networkx graph): The graph.
        revId (str): The revision ID.

    Returns:
        list: List of node's name.
    """
    nodes = []
    for node, attr in graph.nodes.items():
        node_revId = attr.get("idRO", False)
        if node_revId and node_revId == revId:
            nodes.extend(attr.get("trigger"))
            parent_nodes = list(graph.predecessors(node))
            # Loop over all the parents of the existing node
            for parent_node in parent_nodes:
                children = list(graph.successors(parent_node))
                while len(children) > 0:
                    child = children.pop()
                    child_attr = graph.nodes[child]

                    # need to check the revision flags when the added nodes are not just action nodes
                    if child_attr.get("idRO", None) != revId and not child_attr.get(
                        "is_original", True
                    ):
                        nodes.append(child)
                        children.extend(list(graph.successors(child)))
    return list(set(nodes))
