import pydot
from pydot import frozendict, graph_from_dot_file
from GraphComponent.edge import Edge
from GraphComponent.decision_node import DecisionNode
from GraphComponent.parallel_node import ParallelNode
from GraphComponent.context_node import ContextNode
from GraphComponent.action_node import ActionNode
from GraphComponent.goal_node import GoalNode
import re
import pprint

POSSIBLE_NODES = {
    "circle": GoalNode,
    "oval": ContextNode,
    "diamond": DecisionNode,
    "hexagon": ParallelNode,
}

# TODO
# node type by label letter


class Graph:
    def __init__(self, pydot):
        self.pydot_graph = pydot
        self.nodes = {}
        self.edges = []
        self.parse_nodes()
        self.parse_edges()
        self.link_nodes_and_edges()

    def parse_nodes(self):
        nodes = self.pydot_graph.get_node_list()
        for node in nodes:
            # ignoring false nodes
            if node.get_name() in ["node", "edge"]:
                continue

            # default node type, changing it according to the
            new_node = ActionNode
            is_action_node = True
            if "shape" in node.get_attributes():
                new_node = POSSIBLE_NODES.get(node.get_attributes()["shape"], None)
                is_action_node = False

            # ignores revision operators (ros) for now
            if new_node != None:
                label, cost = self.parse_node_label(
                    node.get_attributes()["label"], is_action_node
                )
                self.nodes[label] = new_node(label, cost=cost)

    def parse_edges(self):
        edges = self.pydot_graph.get_edge_list()
        nodes_label = [node_label for node_label in self.nodes.keys()]
        for edge in edges:
            from_node = [edge.get_source()]
            to_node = [edge.get_destination()]

            if type(from_node[0]) == pydot.frozendict:
                from_node = []
                for node in edge.get_source()["nodes"]:
                    if node.upper() in nodes_label:
                        from_node.append(node)

            if type(to_node[0]) == pydot.frozendict:
                to_node = []
                for node in edge.get_source()["nodes"]:
                    if node.upper() in nodes_label:
                        to_node.append(node)

            for f_node in from_node:
                for t_node in to_node:
                    if (f_node.upper() in nodes_label) and (
                        t_node.upper() in nodes_label
                    ):
                        self.edges.append(
                            Edge(
                                f_node.upper(),
                                t_node.upper(),
                                label_values=self.parse_edge_label(
                                    edge.get_attributes().get("label", None)
                                ),
                            )
                        )

    def parse_edge_label(self, label):
        if not label:
            return None
        label, value = re.findall("<(.*) = \[(.*)\]>", label)[0]
        min, max = value.split("..")
        return {
            label: {
                "lower_bound": min,
                "upper_bound": max,
            }
        }

    def parse_node_label(self, label, isActionNode):
        if isActionNode:
            label, cost = label.split("<br/>")
            label = re.findall("<<b>(.*)<\/b>", label)[0]
            if cost != "":
                cost = re.findall("\[cost=(.*)\]", cost)[0]
                return label, cost
            return label, 0
        else:
            return re.findall("<<b>(.*)</b>>", label)[0], None

    def link_nodes_and_edges(self):
        i = 0
        for edge in self.edges:
            self.nodes[edge.from_node].add_out_edge(edge)
            self.nodes[edge.to_node].add_in_edge(edge)

    # def printDot(self):
    #     for n in self.nodes:
    #         print(n, self.nodes[n])
    #         for e in self.nodes[n].out_edges:
    #             print(e)
    #         for e in self.nodes[n].in_edges:
    #             print(e)

def run(path="UseCases\AGFigures\\testcase-5.dot"):
    graphs = graph_from_dot_file(path, encoding="utf-8")
    graph = graphs[0]
    q = Graph(graph)
    return q

if __name__ == "__main__":
    run()