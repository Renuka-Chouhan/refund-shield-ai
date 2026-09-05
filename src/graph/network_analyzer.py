"""
RefundShield AI - Identity & Network Graph Analysis Engine
Constructs heterogeneous identity graphs connecting Customer -> Device -> Phone -> Address -> Payment.
Detects Sybil clusters, multi-account rings, and computes network risk penalties using NetworkX.
"""

import os
import networkx as nx
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional

from src.data.data_loader import load_raw_tables


class IdentityNetworkAnalyzer:
    """
    Constructs and analyzes the identity entity graph to detect coordinated refund syndicates.
    """

    def __init__(self, df_identity_links: Optional[pd.DataFrame] = None, df_customers: Optional[pd.DataFrame] = None):
        if df_identity_links is None or df_customers is None:
            tables = load_raw_tables()
            df_identity_links = tables.get("identity_links", pd.DataFrame())
            df_customers = tables.get("customers", pd.DataFrame())

        self.df_links = df_identity_links
        self.df_customers = df_customers
        self.graph = nx.Graph()
        self._build_graph()

    def _build_graph(self):
        """Constructs the bipartite / heterogeneous entity graph."""
        if self.df_links.empty:
            return

        # Map known fraud customers
        fraud_map = {}
        if not self.df_customers.empty and "previous_fraud_flag" in self.df_customers.columns:
            fraud_map = dict(zip(self.df_customers["customer_id"], self.df_customers["previous_fraud_flag"]))

        for _, row in self.df_links.iterrows():
            cid = str(row["customer_id"])
            addr = str(row.get("address_id", ""))
            phone = str(row.get("phone_hash", ""))
            dev = str(row.get("device_id", ""))
            pf = str(row.get("payment_fingerprint", ""))

            is_fraud = fraud_map.get(cid, 0) == 1

            # Add Customer Node
            self.graph.add_node(cid, node_type="Customer", label=cid, is_fraud=is_fraud)

            # Add Identifier Nodes and Edges
            if dev and dev != "nan":
                dev_node = f"DEV:{dev}"
                self.graph.add_node(dev_node, node_type="Device", label=dev)
                self.graph.add_edge(cid, dev_node, relation="USES_DEVICE")

            if phone and phone != "nan":
                phone_node = f"PH:{phone}"
                self.graph.add_node(phone_node, node_type="Phone", label=phone)
                self.graph.add_edge(cid, phone_node, relation="USES_PHONE")

            if addr and addr != "nan":
                addr_node = f"ADD:{addr}"
                self.graph.add_node(addr_node, node_type="Address", label=addr)
                self.graph.add_edge(cid, addr_node, relation="SHIPS_TO")

            if pf and pf != "nan":
                pf_node = f"PAY:{pf}"
                self.graph.add_node(pf_node, node_type="PaymentFingerprint", label=pf)
                self.graph.add_edge(cid, pf_node, relation="PAYS_WITH")

    def find_fraud_rings(self, min_accounts: int = 2) -> List[Dict[str, Any]]:
        """
        Detects connected components containing multiple distinct customer accounts.
        Returns a list of detected fraud rings with member accounts and shared identifiers.
        """
        rings = []
        components = list(nx.connected_components(self.graph))

        for idx, comp in enumerate(components):
            subgraph = self.graph.subgraph(comp)
            customers = [n for n, d in subgraph.nodes(data=True) if d.get("node_type") == "Customer"]
            
            if len(customers) >= min_accounts:
                devices = [d.get("label") for n, d in subgraph.nodes(data=True) if d.get("node_type") == "Device"]
                phones = [d.get("label") for n, d in subgraph.nodes(data=True) if d.get("node_type") == "Phone"]
                addresses = [d.get("label") for n, d in subgraph.nodes(data=True) if d.get("node_type") == "Address"]
                
                # Check how many accounts in this ring have confirmed fraud flags
                flagged_accounts = [c for c in customers if self.graph.nodes[c].get("is_fraud", False)]

                rings.append({
                    "ring_id": f"RING_{idx + 1:03d}",
                    "account_count": len(customers),
                    "customers": customers,
                    "flagged_accounts_count": len(flagged_accounts),
                    "shared_devices": list(set(devices)),
                    "shared_phones": list(set(phones)),
                    "shared_addresses": list(set(addresses)),
                    "ring_risk_level": "High" if len(flagged_accounts) > 0 or len(customers) >= 3 else "Medium"
                })

        # Sort rings by severity
        rings.sort(key=lambda r: (r["flagged_accounts_count"], r["account_count"]), reverse=True)
        return rings

    def evaluate_customer_network_risk(self, customer_id: str) -> Dict[str, Any]:
        """
        Computes network risk score and penalty points for a given customer.
        """
        cid = str(customer_id)
        if cid not in self.graph:
            return {
                "network_risk_points": 0,
                "ring_size": 1,
                "shared_account_count": 0,
                "is_in_sybil_ring": False,
                "ring_id": None,
                "description": "Customer not linked to other entities in graph."
            }

        # Find connected component for this customer
        comp = nx.node_connected_component(self.graph, cid)
        subgraph = self.graph.subgraph(comp)
        linked_customers = [n for n, d in subgraph.nodes(data=True) if d.get("node_type") == "Customer" and n != cid]
        flagged_neighbors = [n for n in linked_customers if self.graph.nodes[n].get("is_fraud", False)]

        ring_size = len(linked_customers) + 1
        penalty = 0
        reasons = []

        if ring_size >= 4:
            penalty += 20
            reasons.append(f"Linked in large multi-account syndicate ({ring_size} accounts)")
        elif ring_size >= 2:
            penalty += 12
            reasons.append(f"Shares hardware/phone/address with {len(linked_customers)} other account(s)")

        if len(flagged_neighbors) > 0:
            penalty += 15
            reasons.append(f"Directly connected to {len(flagged_neighbors)} confirmed fraudulent account(s)")

        penalty = min(30, penalty)

        return {
            "network_risk_points": penalty,
            "ring_size": ring_size,
            "shared_account_count": len(linked_customers),
            "flagged_connected_accounts": len(flagged_neighbors),
            "is_in_sybil_ring": ring_size >= 2,
            "description": "; ".join(reasons) if reasons else "Clean network profile"
        }

    def get_plotly_graph_elements(self, max_nodes: int = 150) -> Dict[str, Any]:
        """
        Prepares 2D layout coordinates and styling data for interactive Plotly network rendering.
        """
        # Select largest connected components or sample subgraphs
        rings = self.find_fraud_rings(min_accounts=2)
        target_nodes = set()
        for ring in rings[:8]:
            for c in ring["customers"]:
                if c in self.graph:
                    target_nodes.update(nx.node_connected_component(self.graph, c))
            if len(target_nodes) >= max_nodes:
                break

        if not target_nodes:
            target_nodes = list(self.graph.nodes())[:max_nodes]

        sub = self.graph.subgraph(target_nodes)
        pos = nx.spring_layout(sub, seed=42, k=0.35, iterations=40)

        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []

        color_map = {
            "Customer": "#1E88E5",
            "Customer_Fraud": "#E53935",
            "Device": "#8E24AA",
            "Phone": "#43A047",
            "Address": "#FB8C00",
            "PaymentFingerprint": "#00ACC1"
        }

        for node in sub.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            d = sub.nodes[node]
            ntype = d.get("node_type", "Unknown")
            lbl = d.get("label", node)
            is_f = d.get("is_fraud", False)

            if ntype == "Customer" and is_f:
                c = color_map["Customer_Fraud"]
                sz = 16
                node_text.append(f"<b>Flagged Customer:</b> {lbl}")
            elif ntype == "Customer":
                c = color_map["Customer"]
                sz = 14
                node_text.append(f"<b>Customer:</b> {lbl}")
            else:
                c = color_map.get(ntype, "#757575")
                sz = 10
                node_text.append(f"<b>{ntype}:</b> {lbl}")

            node_color.append(c)
            node_size.append(sz)

        edge_x = []
        edge_y = []
        for edge in sub.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        return {
            "node_x": node_x,
            "node_y": node_y,
            "node_text": node_text,
            "node_color": node_color,
            "node_size": node_size,
            "edge_x": edge_x,
            "edge_y": edge_y,
            "total_nodes": len(sub.nodes()),
            "total_edges": len(sub.edges()),
            "rings_detected": len(rings)
        }


if __name__ == "__main__":
    analyzer = IdentityNetworkAnalyzer()
    rings = analyzer.find_fraud_rings()
    print(f"[NetworkAnalyzer] Total entities: {analyzer.graph.number_of_nodes()}, edges: {analyzer.graph.number_of_edges()}")
    print(f"[NetworkAnalyzer] Detected {len(rings)} multi-account rings.")
    if rings:
        print("Top detected fraud ring:", rings[0])
        sample_c = rings[0]["customers"][0]
        print(f"Risk evaluation for {sample_c}:", analyzer.evaluate_customer_network_risk(sample_c))
