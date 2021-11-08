from utils import (
    find_goal_node,
    find_init_node,
    find_parallel_path,
    find_revId_involved_nodes,
    get_all_metrics,
    get_all_revIds,
    get_metric_name,
    get_type_nodes,
)


def write_objects(graph, file):
    # might be able to refactor this into a function that returns {diseases, node, revId} once we'll add RO
    disease = get_type_nodes(graph, "context")
    nodes = [node for node in graph.nodes if graph.nodes[node]["type"] != "context"]
    file.write("(:objects {} - disease\n".format(" ".join(disease)))
    file.write(
        "\t" * 3 + "{} - node\n".format(" ".join(nodes))
    )  # TODO: add parallel nodes
    file.write("\t" * 3 + "{} - revId\n".format(" ".join(get_all_revIds(graph))))
    file.write(")\n")


def write_initial_state(graph, file, ros):
    file.write("(:init ")
    # decision branching min/max
    write_decision_branch(graph, file)
    file.write("\n")

    # patient value - NOT NOW
    # noPrevious nodes
    # write_not_previous_node(graph, file)
    # file.write("\n")

    # predecessorNode
    init_nodes = get_type_nodes(graph, "context")

    nodes = []
    predecessor = []
    original_node = []
    parallel_node_found = []

    revisionAction = []

    # TODO - work on parrallel Node
    for name, attributes in graph.nodes.items():
        node_type = attributes["type"]

        if node_type not in ["context", "goal", "parallel"]:
            nodes.append("\t({}Node {})\n".format(node_type, name))
        else:
            if node_type == "context":
                file.write(
                    "\t(initialNode {} {})\n".format(
                        name, list(graph.out_edges(name))[0][1]
                    )
                )
                file.write(
                    "\t(goalNode {} {})\n".format(name, find_goal_node(graph, name))
                )

            # Parallel node found
            if node_type == "parallel":
                parallel_node_found.append(name)

        for pred in graph.predecessors(name):
            if pred not in init_nodes:
                predecessor.append("\t(predecessorNode {} {})\n".format(pred, name))

        # originalAction - added is_original to action nodes
        if attributes.get("is_original") == True:
            original_node.append("\t(originalAction {})\n".format(name))

        # revisionAction
        if attributes.get("is_original") == False:
            revisionAction.append("\t(revisionAction {})\n".format(name))

    # Parallel nodes processing
    parallel_node = find_parallel_path(graph, parallel_node_found)

    file.write("\n\t")
    file.write("".join(parallel_node))
    file.write("\n")
    file.write("".join(predecessor))
    file.write("\n")
    file.write("".join(nodes))
    file.write("\n")
    file.write("".join(original_node))

    # revisionAction - NOT NOW
    file.write("\n")
    file.write("".join(revisionAction))

    # revision flag - NOT NOW
    file.write("\n")
    write_revision_flags(graph, file, ros)
    file.write("\n")
    write_all_revisions_pass(graph, file)
    # tentativeGoalCount - ???
    # numgoals
    file.write("\n")
    file.write("\t(= (numGoals) {})\n".format(len(get_type_nodes(graph, "goal"))))

    # nodeCost - ask with afib example for different costs
    file.write("\n")
    write_node_cost(graph, file)

    # total-cost - ??
    file.write("\n")
    write_total_metrics(graph, file)
    file.write(")\n")


def write_total_metrics(graph, file):
    metrics = get_all_metrics(graph)
    for metric in metrics:
        metric_name = get_metric_name(metric)
        file.write("\t(= (total-{}) 0)\n".format(metric_name.lower()))


def write_decision_branch(graph, file):
    decision_nodes = get_type_nodes(graph, "decision")
    for node in decision_nodes:
        for _, out_edge in graph.out_edges(node):
            lower, upper = graph[node][out_edge][0]["range"].split("..")
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
    init_nodes = get_type_nodes(graph, "context")
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
    init_nodes = get_type_nodes(graph, "context")
    for node in init_nodes:
        to_node = list(graph.out_edges(node))[0][1]
        to_node_type = graph.nodes[to_node]["type"]
        file.write("\t(noPrevious{} {})\n".format(to_node_type.capitalize(), node))


def write_goal(graph, file):
    goal_nodes = [node for node in graph.nodes if graph.nodes[node]["type"] == "goal"]
    file.write("(:goal ")
    if len(goal_nodes) > 1:
        file.write("(and")
    for node in goal_nodes:
        find_init_node(graph, node)
        file.write(
            "\t(treatmentPlanReady {} {})\n".format(find_init_node(graph, node), node)
        )
    file.write(")\n")


# TODO - revise this, no weights input for now
def write_metric(graph, file):
    file.write("(:metric minimize (+\n")
    metrics = get_all_metrics(graph)
    for metric in metrics:
        metric_name = get_metric_name(metric)
        file.write("\t(total-{})\n".format(metric_name.lower()))
    file.write("\t)\n)\n ")


def write_all_revisions_pass(graph, file):
    disease = get_type_nodes(graph, "context")
    for d in disease:
        file.write("\t(= (allRevisionsPass {}) 0)\n".format(d))


def write_revision_flags(graph, file, ros):
    disease = get_type_nodes(graph, "context")
    for ro in ros:
        revId = ro["id"]
        nodes_to_flag = find_revId_involved_nodes(graph, revId)
        for node, attr in graph.nodes.items():
            if attr.get("type") == "context":
                continue
            file.write(
                "\t(= (revisionFlag {} {}) {})\n".format(
                    node, revId, 1 if node in nodes_to_flag else 0
                )
            )
        file.write("\n")
        file.write(
            "\t(= (revisionSequenceNumNodes {}) {})\n".format(revId, len(ro["trigger"]))
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


def outputPDDL(graph, ros, problem_name, domain_name):
    with open("problem.pddl", "w") as pddl:
        # define
        pddl.write(("(define (problem {})\n").format(problem_name))
        pddl.write(("\t(:domain  {})\n").format(domain_name))

        # objects
        write_objects(graph, pddl)

        # :init
        pddl.write("\n")
        write_initial_state(graph, pddl, ros)

        # :goal
        pddl.write("\n")
        write_goal(graph, pddl)

        # :metric
        pddl.write("\n")
        write_metric(graph, pddl)
        pddl.write(")")
        pddl.close()

        # Debugging
        # for node in graph.nodes:
        #     print(node+ "=="+str(graph.nodes[node]))