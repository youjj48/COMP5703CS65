from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable

uri = "neo4j+s://227816f4.databases.neo4j.io"
user = "neo4j"
password = "0A2TcqorfsDg-ai2Brr3YUDuHnYR3UGyeOm5dcWKHgo"


class App:
    label_relation = {"Symptom": "HAS_SYMPTON", "Cause": "CAUSE", "Disease": "COMPLICATION", "Prevention": "PREVENT",
                      "Treatment": "TREAT", "Diagnosis": "DIAGNOSE"}

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_relationship(self, write_disease_name, write_node_label, write_node_name):
        with self.driver.session() as session:
            result = session.write_transaction(
                self._create_and_return_relationship, write_disease_name, write_node_label, write_node_name)
            for row in result:
                result_creation = (
                    "Created relation:{r} between: {p1}, {p2}".format(r=App.label_relation[write_node_label],
                                                                      p1=row['p1'], p2=row['p2']))
                print(result_creation)

            return result_creation

    @staticmethod
    def _create_and_return_relationship(tx, write_disease_name, write_node_label, write_node_name):
        write_relation = App.label_relation[write_node_label]
        query = (
            "MERGE (p1:Disease { name: $write_disease_name }) "
            "WITH p1 "
            "CALL apoc.merge.node([ $write_node_label ], {name: $write_node_name}) YIELD node as p2 "
            "CALL apoc.create.relationship(p1, $write_relation, {}, p2) YIELD rel "
            "RETURN p1, p2"
        )
        result = tx.run(query, write_disease_name=write_disease_name, write_node_label=write_node_label,
                        write_node_name=write_node_name, write_relation=write_relation)
        try:
            return [{"p1": row["p1"]["name"], "p2": row["p2"]["name"]}
                    for row in result]
        # Capture any errors along with the query and data for traceability
        except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                query=query, exception=exception))
            raise

    def find_node(self, label, disease_name):
        with self.driver.session() as session:
            disease_name_query = str(disease_name)
            label_name = str(label)
            query = (
                    "MATCH relation=(d:" + label_name + ")--(node)"
                                                        f"WHERE d.name = \"{disease_name_query}\" "
                                                        "RETURN relation"
            )
            result = session.read_transaction(self._find_and_return_node, label, disease_name)
            result_find_list = []
            result_find = {}
            output = {}
            for node in result:
                result_find["Relation"] = node[0]
                result_find["Node content"] = str(node[1])
                tem_result_find = result_find.copy()
                result_find_list.append(tem_result_find)

            output['find'] = result_find_list
            output['query'] = query

            return output

    @staticmethod
    def _find_and_return_node(tx, label, node_name):
        query = (
                "MATCH relation=(d:" + label + ")--(node)"
                                               "WHERE d.name = $node_name "
                                               "RETURN relation"
        )
        result = tx.run(query, label=label, node_name=node_name)
        # ipdb.set_trace()
        return_list = []
        for row in result:
            return_dict = row.data()
            node_label = return_dict['relation'][1]
            node_value = return_dict['relation'][2]['name']
            # print(node_label,node_value)
            return_list.append([node_label, node_value])
        return return_list

    def delete_node(self, node_label, node_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._delete_node, node_label, node_name)
            # print(result)
            print("Node", node_name, "and connected relation has been deleted")
            result_delete = ("Node", node_name, "and connected relation has been deleted")

            return result_delete

    @staticmethod
    def _delete_node(tx, node_label, node_name):
        query = (
            "MATCH (n {name: $node_name })"
            "DETACH DELETE n"
        )
        result = tx.run(query, node_label=node_label, node_name=node_name)
        return result

    def modify_node(self, node_label, node_name, after_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._modify_node, node_label, node_name, after_name)
            print("{n1} has been changed to {n2}".format(n1=node_name, n2=after_name))
            result_modify = ("{n1} has been changed to {n2}".format(n1=node_name, n2=after_name))

            return result_modify

    @staticmethod
    def _modify_node(tx, node_label, node_name, after_name):
        query = (
            "MATCH (n{name: $node_name })"
            "SET n.name = $after_name "
            "RETURN n"
        )
        result = tx.run(query, node_label=node_label, node_name=node_name, after_name=after_name)
        return result

    @staticmethod
    def _find_distinct_node_rel_node(tx):
        query = (
            "MATCH (a)-[r]->(b)"
            "RETURN DISTINCT labels(a) AS a, TYPE(r) AS r, labels(b) AS b"
        )
        result = tx.run(query)
        return_list = []
        for row in result:
            return_dict = row.data()
            node_a = return_dict['a']
            relation = return_dict['r']
            node_b = return_dict['b']

            return_list.append([node_a, relation, node_b])
        return return_list

    def find_distinct_node_rel_node(self):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_distinct_node_rel_node)
            list = {}
            all_list = []
            for node in result:
                list["label_1"] = format(node[0][0])
                list["relation"] = str(format(node[1]))
                list["label_2"] = str(format(node[2][0]))
                l_list = list.copy()
                all_list.append(l_list)
            return(all_list)

    def get_nodes(self):
        with self.driver.session() as session:
            result = session.read_transaction(self._get_nodes)
            list = {}
            all_list = []
            for node in result:
                list["Label name"] = format(node[0])
                list["Counts"] = str(format(node[1]))
                l_list = list.copy()
                all_list.append(l_list)
            return all_list

    @staticmethod
    def _get_nodes(tx):
        query = ("MATCH (n) RETURN distinct labels(n), count(*)")
        result = tx.run(query)
        return_list = []
        for row in result:
            return_dict = row.data()
            node_label = return_dict['labels(n)'][0]
            node_value = (return_dict['count(*)'])
            return_list.append([node_label, node_value])
        return return_list
