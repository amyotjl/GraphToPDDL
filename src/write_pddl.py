from src.CONSTANTS import (
    DATA_ITEM_ATTR,
    DECISION_NODE,
    GOAL_NODE,
    CONTEXT_NODE,
    ID_RO,
    IS_ORIGINAL_ATTR,
    PARALLEL_NODE,
    RANGE_ATTR,
    TRIGGER,
    TYPE_ATTR,
    DEFAULT_PATIENT_VALUE,
)
from src.utils import (
    find_goal_node,
    find_init_node,
    find_parallel_path,
    match_nodes_to_disease,
    find_revId_involved_nodes,
    get_all_metrics,
    get_all_revIds,
    get_metric_name,
    get_type_nodes,
    get_number_parallel_paths,
)


def write_objects(graph, file):
    """
    Writes the objects (disease, node and revId) to the file.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    disease = get_type_nodes(graph, CONTEXT_NODE)
    nodes = [
        node for node in graph.nodes if graph.nodes[node][TYPE_ATTR] != CONTEXT_NODE
    ]
    file.write("(:objects {} - disease\n".format(" ".join(disease)))
    file.write("\t" * 3 + "{} - node\n".format(" ".join(nodes)))
    file.write("\t" * 3 + "{} - revId\n".format(" ".join(get_all_revIds(graph))))
    file.write(")\n")


def write_initial_state(graph, file, ros, patient_values):
    """
    Writes all the predicates of the initial (:init) state to the file.

    Calls a subfunction for each predicates in the initial state

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
        ros (list) : List of revision operators.
        patient_values (dict) : Dictonary of the patient values.

    """
    file.write("(:init ")
    # decision branching min/max
    write_decision_branch(graph, file)
    file.write("\n")

    # patient value
    if patient_values:
        patient_values[DEFAULT_PATIENT_VALUE] = 0
        write_patient_values(graph, file, patient_values)
        file.write("\n")

    # noPrevious nodes
    write_not_previous_node(graph, file)
    file.write("\n")

    # initialNode
    # goalNode
    # predecessorNode
    # node type
    # originalAction
    # revisionAction
    write_predecessors_and_node_type(graph, file)

    # revision flag
    file.write("\n")
    write_revision_flags(graph, file, ros)
    file.write("\n")
    write_all_revisions_pass(graph, file)

    # numRevisionIDs
    write_num_revision_Ids(graph, file)
    file.write("\n")

    # anyRevisionOps | noRevisionOps
    write_any_no_revision_ops(graph, file, ros)
    file.write("\n")
    # tentativeGoalCount
    write_tentative_goal_count(graph, file)
    # numgoals
    file.write("\n")
    file.write("\t(= (numGoals) {})\n".format(len(get_type_nodes(graph, GOAL_NODE))))

    # nodeCost - ask with afib example for different costs
    file.write("\n")
    write_node_cost(graph, file)

    # total-cost - ??
    file.write("\n")
    write_total_metrics(graph, file)
    file.write(")\n")


def write_predecessors_and_node_type(graph, file):
    """
    Write the following predicates to the file:

    - predecessorNode
    - originalAction
    - node type (e.g. actionNode)
    - revisionAction
    - parallelStartNode
    - parallelEndNode
    - parallel node type
    - untraversedParallelNode

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    init_nodes = get_type_nodes(graph, CONTEXT_NODE)

    nodes = []
    predecessor = []
    original_node = []
    parallel_node_found = []
    revisionAction = []

    for name, attributes in graph.nodes.items():
        node_type = attributes[TYPE_ATTR]

        if node_type not in [CONTEXT_NODE, GOAL_NODE, PARALLEL_NODE]:
            nodes.append("\t({}Node {})\n".format(node_type, name))
        else:
            if node_type == CONTEXT_NODE:
                file.write(
                    "\t(initialNode {} {})\n".format(
                        name, list(graph.out_edges(name))[0][1]
                    )
                )
                file.write(
                    "\t(goalNode {} {})\n".format(name, find_goal_node(graph, name))
                )

            # Parallel node found
            if node_type == PARALLEL_NODE:
                parallel_node_found.append(name)

        for pred in graph.predecessors(name):
            if pred not in init_nodes:
                predecessor.append("\t(predecessorNode {} {})\n".format(pred, name))

        # originalAction - added is_original to action nodes
        if attributes.get(IS_ORIGINAL_ATTR) == True:
            original_node.append("\t(originalAction {})\n".format(name))

        # revisionAction
        if attributes.get(IS_ORIGINAL_ATTR) == False:
            revisionAction.append("\t(revisionAction {})\n".format(name))


    file.write("\n")
    file.write("".join(predecessor))
    file.write("\n")
    file.write("".join(nodes))
    file.write("\n")
    file.write("".join(original_node))

    
    # Parallel nodes processing
    parallel_node = find_parallel_path(graph, parallel_node_found)

    file.write("\n\t")
    file.write("".join(parallel_node))

    # number of parallel paths
    n_path_found = get_number_parallel_paths(graph)
    if parallel_node_found:
        [
            file.write("".join(f"\n\t(= (parallelPathCount {init_node} {find_init_node(graph,init_node)}) 0)"))
            for init_node, n_paths in n_path_found.items()
        ]
        [
            file.write("".join(f"\n\t(= (numParallelPaths {init_node} {find_init_node(graph,init_node)}) {n_paths})"))
            for init_node, n_paths in n_path_found.items()
        ]
    file.write("\n\t")
    
    # revisionAction
    file.write("\n")
    file.write("".join(revisionAction))


def write_total_metrics(graph, file):
    """
    Writes the total metrics predicates.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    metrics = get_all_metrics(graph)
    for metric in metrics:
        metric_name = get_metric_name(metric)
        file.write("\t(= (total-{}) 0)\n".format(metric_name.lower()))


def write_tentative_goal_count(graph, file):
    """
    Writes the tentative goal count predicate. Currently is hardcoded to 0.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    file.write("\t(= (tentativeGoalCount) 0)\n")


def write_decision_branch(graph, file):
    """
    Writes the decision branch min/max predicates (e.g. decisionBranchMax).

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    decision_nodes = get_type_nodes(graph, DECISION_NODE)
    for node in decision_nodes:
        for _, out_edge in graph.out_edges(node):
            lower, upper = graph[node][out_edge][0][RANGE_ATTR].split("..")
            file.write(
                "\t(= (decisionBranchMin {} {} {}) {})\n".format(
                    find_init_node(graph, node), node, out_edge, lower
                )
            )
            file.write(
                "\t(= (decisionBranchMax {} {} {}) {})\n".format(
                    find_init_node(graph, node), node, out_edge, upper
                )
            )


def write_node_cost(graph, file):
    """
    Writes node costs predicates.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    init_nodes = get_type_nodes(graph, CONTEXT_NODE)
    metrics = get_all_metrics(graph)
    for metric in metrics:
        for node, attr in graph.nodes.items():
            if node not in init_nodes:
                metric_name = get_metric_name(metric)
                metric_name = metric_name[0].upper() + metric_name[1:]
                file.write(
                    "\t(= (node{} {}) {})\n".format(
                        metric_name, node, attr.get(metric, 0)
                    )
                )
        file.write("\n")


def write_not_previous_node(graph, file):
    """
    Writes the no previous predicates (e.g: noPreviousDecision).

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    init_nodes = get_type_nodes(graph, CONTEXT_NODE)
    for node in init_nodes:
        to_node = list(graph.out_edges(node))[0][1]
        to_node_type = graph.nodes[to_node][TYPE_ATTR]
        # noPreviousParallel fix
        if to_node_type != PARALLEL_NODE:
            file.write("\t(noPrevious{} {})\n".format(to_node_type.capitalize(), node))


def write_goal(graph, file):
    """
    Writes treatment plan ready predicate in the goal section of the PDDL file.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    goal_nodes = [
        node for node in graph.nodes if graph.nodes[node][TYPE_ATTR] == GOAL_NODE
    ]
    file.write("(:goal ")
    if len(goal_nodes) > 1:
        file.write("(and")
    for node in goal_nodes:
        find_init_node(graph, node)
        file.write(
            "\t(treatmentPlanReady {} {})\n".format(find_init_node(graph, node), node)
        )
    file.write("\t)\n)\n")


# TODO - revise this, no weights input for now
def write_metric(graph, file):
    """
    Writes the metric section of the PDDL file with all the metrics found in the graph.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    file.write("(:metric minimize")
    metrics = get_all_metrics(graph)
    if len(metrics) > 1:
        file.write("(+\n")

    for metric in metrics:
        metric_name = get_metric_name(metric)
        file.write("\t(total-{})\n".format(metric_name.lower()))

    file.write(")\n ")
    if len(metrics) > 1:
        file.write(")\n ")


def write_all_revisions_pass(graph, file):
    """
    Writes all revision pass predicate.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    disease = get_type_nodes(graph, CONTEXT_NODE)
    for d in disease:
        file.write("\t(= (allRevisionsPass {}) 0)\n".format(d))


def write_revision_flags(graph, file, ros):
    """
    Writes treatment plan ready predicate in the goal section of the PDDL file.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
        ros (list) : The list of revision operator objects
    """
    disease = get_type_nodes(graph, CONTEXT_NODE)
    for ro in ros:
        revId = ro["id"]
        nodes_to_flag = find_revId_involved_nodes(graph, revId)
        for node, attr in graph.nodes.items():
            if attr.get(TYPE_ATTR) == CONTEXT_NODE:
                continue
            file.write(
                "\t(= (revisionFlag {} {}) {})\n".format(
                    node, revId, 1 if node in nodes_to_flag else 0
                )
            )
        file.write("\n")
        file.write(
            "\t(= (revisionSequenceNumNodes {}) {})\n".format(revId, len(ro[TRIGGER]))
        )
        file.write(
            "\t(= (numNodesToReplace {}) {})\n".format(
                revId, len(ro.get("operations", 0))  # not sure...
            )
        )
        file.write("\t(= (revisionCount {}) 0)\n".format(revId))
        for d in disease:
            file.write("\t(= (revisionIDPass {} {}) 0)\n".format(d, revId))
        file.write("\n")


def write_num_revision_Ids(graph, file):
    """
    Writes the numRevisionIDs predicate to the PDDL file.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
    """
    ro_diseases = match_nodes_to_disease(graph)
    for disease, ro in ro_diseases.items():
        file.write("\t(= (numRevisionIDs {}) {})\n".format(disease, len(ro)))


def write_patient_values(graph, file, patient_values):
    """
    Writes the patient value predicate. There is one predicate per successor
    each decision node.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
        patient_values (dict) : Dictonary of the patient values.

    """
    for node, attr in graph.nodes.items():
        if attr[TYPE_ATTR] == DECISION_NODE:
            disease = find_init_node(graph, node)
            file.write(
                "\n\t;; {} = {}\n".format(
                    attr[DATA_ITEM_ATTR], patient_values[attr[DATA_ITEM_ATTR]]
                )
            )
            for successor in graph.successors(node):
                file.write(
                    "\t(= (patientValue {} {} {}) {})\n".format(
                        disease, node, successor, patient_values[attr[DATA_ITEM_ATTR]]
                    )
                )


def write_any_no_revision_ops(graph, file, ros):
    """
    Writes anyRevisionOps or noRevsionOps predicates.

    Args:
        graph (networkx graph): The graph.
        file (TextIOWrapper): The PDDL file.
        ros (list) : The list of revision operator objects
    """
    all_triggers = [trigger for ro in ros for trigger in ro[TRIGGER]]
    all_triggers = list(set(all_triggers))
    diseases = get_type_nodes(graph, CONTEXT_NODE)
    any_revision_ops = []

    for trigger in all_triggers:
        disease = find_init_node(graph, trigger)

        if not disease in any_revision_ops:
            diseases.remove(disease)
            any_revision_ops.append(disease)

    for rev_op in any_revision_ops:
        file.write("\t(anyRevisionOps {})\n".format(rev_op))

    for rev_op in diseases:
        file.write("\t(noRevisionOps {})\n".format(rev_op))


def outputPDDL(graph, ros, patient_values, problem_name, domain_name, output_dir):
    """
    Ouputs the PDDL file.

    Args:
        graph (networkx graph): The graph.
        ros (list) : The list of revision operator objects
        patient_values (dict) : Dictonary of the patient values.
        problem_name (str): The name of the problem to be in the PDDL file.
        domain_name (str): The name of the domain to be in the PDDL file.
    """
    with open(
        "{}{}{}.pddl".format(output_dir, "/" if output_dir else "", problem_name), "w"
    ) as pddl:
        # define
        pddl.write(("(define (problem {})\n").format(problem_name))
        pddl.write(("\t(:domain  {})\n").format(domain_name))

        # objects
        write_objects(graph, pddl)

        # :init
        pddl.write("\n")
        write_initial_state(graph, pddl, ros, patient_values)

        # :goal
        pddl.write("\n")
        write_goal(graph, pddl)

        # :metric
        pddl.write("\n")
        write_metric(graph, pddl)
        pddl.write(")")
        pddl.close()
