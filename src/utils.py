import networkx as nwx

from src.CONSTANTS import (
    ACTION_NODE,
    ALTERNATIVE_NODE,
    CONTEXT_NODE,
    DATA_ITEM_ATTR,
    DECISION_NODE,
    ID_RO,
    IS_ALTERNATIVE,
    IS_IN_PARALLEL,
    IS_ORIGINAL_ATTR,
    PARALLEL_NODE,
    PARALLEL_START_ATTR,
    PARLLEL_END_ATTR,
    RANGE_ATTR,
    TRIGGER,
    TYPE_ATTR,
)


def get_type_nodes(graph, node_type):
    """
    Retrieves list of nodes of the given type

    Args:
        graph (networkx graph): The graph.
        node_type (str): Type of the nodes to retrieve.

    Returns:
        list: List of node of the given type.

    """
    return [node for node, attr in graph.nodes.items() if attr[TYPE_ATTR] == node_type]


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

        if attributes.get(IS_IN_PARALLEL) == True:
            parallel_nodes.append(f"{node}")

    return parallel_nodes


def get_number_parallel_paths(graph):
    """
    Finds the number of parallel paths for each diseases.

    Args:
        graph (networkx graph): The graph.

    Returns:
        int: Number of parallel paths.
    """  # find_init_node
    p_start = []
    p_end = []
    n_path_found = {}
    for node, attributes in graph.nodes.items():
        if find_init_node(graph, node) not in n_path_found:
            n_path_found[find_init_node(graph, node)] = 0
        if attributes.get(PARALLEL_START_ATTR) == True:
            # print(node)
            p_start.append(node)
        if attributes.get(PARLLEL_END_ATTR) == True:
            # print(node)
            p_end.append(node)


    # print(p_start)
    # print(p_end)
    # print(n_path_found)
    for start in p_start:
        for end in p_end:
            if start != "" and end != "":
                # print("==========")
                # print(start)
                # print(end)
                parallel_sequence = list(
                    nwx.all_simple_paths(graph, source=start, target=end)
                )
                n_paths = len(parallel_sequence)
                context = find_init_node(graph, start)
                # print(parallel_sequence)
                # print(n_paths)
                # print(context)
                n_path_found[context] = n_paths + n_path_found.get(context, 0)
                
    # print(n_path_found)
    return n_path_found


def find_parallel_path(graph, p_nodes_found):
    """
    Finds all parallel paths from a list of parallel nodes.

    Args:
        graph (networkx graph): The graph.
        p_nodes_found (list): List of parallel start and end nodes.


    Returns:
        str: PDDL representation of the parallel path.

    """
    parallelNode = ""
    # TODO: numParallelPaths for each diseases
    end_nodes = []

    for start_node in p_nodes_found:

        # TODO: Check whether this will make it more robust with a bigger graph
        # Check if the current start node is an en d node
        if start_node not in end_nodes:
            for end_node in p_nodes_found:

                if graph.nodes[end_node].get(PARLLEL_END_ATTR): # Only end nodes
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
                        graph.nodes[start_node][PARALLEL_START_ATTR] = True
                        if end_node not in end_nodes:
                            end_nodes.append(end_node)
                            parallelNode += "(parallelEndNode {})\n\t".format(end_node)
                            graph.nodes[end_node][PARLLEL_END_ATTR] = True

                        # print("==")
                        # print(start_node)
                        # print(end_node)
                        # for path in parallel_sequence:
                        (
                            toParallelNode
                        ) = update_between_parallel_nodes(
                            graph,
                            start_node,
                            end_node,
                            []
                        )

                        
                        # print(toParallelNode)
                        
                        untraversedParallelNode += "(untraversedParallelNode {})\n\t".format(start_node)
                        for p_nodes in list(toParallelNode):
                            if graph.nodes[p_nodes][TYPE_ATTR] != PARALLEL_NODE:
                                graph.nodes[p_nodes][IS_IN_PARALLEL] = True
                                
                                parallelTypeNode += "(parallel{}Node {})\n\t".format(
                                    graph.nodes[p_nodes][TYPE_ATTR].capitalize(), p_nodes
                                )
                            if p_nodes != end_node:
                                untraversedParallelNode += "(untraversedParallelNode {})\n\t".format(p_nodes)
                        untraversedParallelNode += "(untraversedParallelNode {})\n\t".format(end_node)
                        
                        parallelNode += parallelTypeNode
                        parallelNode += untraversedParallelNode

                    

    return parallelNode


def update_between_parallel_nodes(
    graph,
    start_node,
    end_node,
    toParallelNode=[],
):
    """
    Updates the PDDL representation of the parallel nodes between a parallel start node and a parallel end node.



    Args:
        graph (networkx graph): The graph.
        start_node (str): Start node of the parallel path, Parallel Start Node.
        end_node (str): End node of the parallel path, Parallel End Node.
        toParallelNode (lst): List of nodes in parallels.

    Returns:
        str: PDDL representation of the parallel nodes.
    """
    if start_node == end_node:
        # print("===")
        # print(toParallelNode)
        return toParallelNode

    if type(start_node) == str:
        # Print here can be used to see all the different paths
        # print("===")
        # print(start_node)
        # print(end_node)
        # print(graph.out_edges(start_node))
        if graph.out_edges(start_node):
            first_path, *path_list = graph.out_edges(start_node)
        else:
            first_path = [start_node, end_node]
            path_list = []
        # print(first_path)
        
    else:
        first_path, *path_list = start_node
        



    # print("===")
    # print(first_path)
    # print(path_list)
    if len(path_list) == 1:
        # print("decision")
        _, node = path_list.pop()
        _, nodefp = first_path

        if nodefp not in toParallelNode:
            toParallelNode.append(nodefp)

        toParallelNode = update_between_parallel_nodes(
            graph,
            nodefp,
            end_node,
            toParallelNode
        )
        return update_between_parallel_nodes(
            graph,
            node,
            end_node,
            toParallelNode
        )

    elif len(path_list) > 1:
        #print("decisions")
        # print(start_node)
        _, nodefp = first_path
        if nodefp not in toParallelNode:
            toParallelNode.append(nodefp)

        toParallelNode = update_between_parallel_nodes(
            graph,
            nodefp,
            end_node,
            toParallelNode
        )

        return update_between_parallel_nodes(
            graph,
            path_list,
            end_node,
            toParallelNode
        )
    

    _, node = first_path
    if start_node not in toParallelNode:
        toParallelNode.append(start_node)
    if node not in toParallelNode:
        toParallelNode.append(node)
    return update_between_parallel_nodes(
        graph,
        node,
        end_node,
        toParallelNode
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
    action_nodes = get_type_nodes(graph, ACTION_NODE)
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
        idRO = attr.get(ID_RO, False)
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
        node_revId = attr.get(ID_RO, False)
        if node_revId and node_revId == revId:
            nodes.extend(attr.get(TRIGGER))
            parent_nodes = list(graph.predecessors(node))
            # Loop over all the parents of the existing node
            for parent_node in parent_nodes:
                children = list(graph.successors(parent_node))
                while len(children) > 0:
                    child = children.pop()
                    child_attr = graph.nodes[child]
                    child_id_ro = child_attr.get(ID_RO, None)
                    # need to check the revision flags when the added nodes are not just action nodes
                    if child_id_ro and child_id_ro != revId:
                        print(revId, child)
                        nodes.append(child)
                        children.extend(list(graph.successors(child)))
    return list(set(nodes))


def match_nodes_to_disease(graph):
    """
    For each disease, find the revision operators that involve the disease.

    Format of the return object:

        {
            "disease1": ['ro1', 'ro2'],
            ...
        }


    Args:
        graph (networkx graph): The graph.

    Returns:
        object: Object where the keys are the diseases and the values are a list of revision operations IDs.
    """
    revIds = get_all_revIds(graph)
    diseases = get_type_nodes(graph, CONTEXT_NODE)

    ro_disease = {}
    for disease in diseases:
        ro_disease[disease] = set()

    for revId in revIds:
        nodes = find_revId_involved_nodes(graph, revId)
        diseases_involved = []
        for node in nodes:
            diseases_involved.append(find_init_node(graph, node))
        for disease in diseases_involved:
            ro_disease[disease].add(revId)
    return ro_disease


def handle_alternative_nodes(graph):
    """
    Modifies the alternative nodes to decision nodes where all successors have the same edges value.
    That way, the planner will look into all successors for an optimize solution.


    The patient values provided should include a value called "default" with the value of 0 or 1 that will be used for the alternative nodes.

    Args:
        graph (networkx graph): The graph.
    """
    for node, attr in graph.nodes.items():
        if attr.get(TYPE_ATTR) == ALTERNATIVE_NODE:
            graph.nodes[node][TYPE_ATTR] = DECISION_NODE
            graph.nodes[node][DATA_ITEM_ATTR] = "default_value"
            graph.nodes[node][IS_ALTERNATIVE] = True
            for succ in graph.successors(node):
                graph.edges[node, succ, 0][RANGE_ATTR] = "0..1"
