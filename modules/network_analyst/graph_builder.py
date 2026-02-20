"""
Construtor de grafos para análise de redes políticas.
Usa NetworkX para criar grafos bipartidos deputado ↔ frente e calcular métricas de centralidade.
"""

import networkx as nx
from networkx.algorithms import bipartite


def build_graph(frente_membro_map: dict[int, list[dict]], frentes_info: list[dict]) -> nx.Graph:
    """
    Cria um grafo bipartido onde:
    - Nós do tipo 'frente' representam frentes parlamentares
    - Nós do tipo 'deputado' representan deputados
    - Arestas conectam deputados às suas frentes

    Args:
        frente_membro_map: {frente_id → [lista de membros]}
        frentes_info: Lista de dicionários com informações das frentes (id, titulo)

    Returns:
        Grafo NetworkX com atributos nos nós.
    """
    G = nx.Graph()

    # Indexar frentes por id
    frentes_index = {f["id"]: f for f in frentes_info if "id" in f}

    for frente_id, membros in frente_membro_map.items():
        info = frentes_index.get(frente_id, {})
        frente_label = f"F:{frente_id}"

        # Adicionar nó de frente
        G.add_node(
            frente_label,
            tipo="frente",
            id=frente_id,
            titulo=info.get("titulo", f"Frente {frente_id}"),
            bipartite=0,
        )

        for membro in membros:
            dep_id = membro.get("id")
            if not dep_id:
                continue

            dep_label = f"D:{dep_id}"

            # Adicionar nó de deputado (se ainda não existe)
            if dep_label not in G:
                G.add_node(
                    dep_label,
                    tipo="deputado",
                    id=dep_id,
                    nome=membro.get("nome", f"Deputado {dep_id}"),
                    partido=membro.get("siglaPartido", "N/A"),
                    uf=membro.get("siglaUf", "N/A"),
                    bipartite=1,
                )

            # Criar aresta deputado ↔ frente
            G.add_edge(dep_label, frente_label)

    print(f"[graph_builder] Grafo criado: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas.")
    return G


def get_bridge_nodes(G: nx.Graph, top_n: int = 20) -> list[tuple[str, float]]:
    """
    Identifica os nós 'ponte' (deputados com alta centralidade de intermediação).
    Deputados que aparecem em múltiplas frentes formam pontes entre grupos.

    Args:
        G: Grafo construído com build_graph().
        top_n: Quantidade de nós de maior centralidade a retornar.

    Returns:
        Lista de (nó, betweenness_centrality) ordenada do maior para o menor.
    """
    print("[graph_builder] Calculando centralidade de intermediação (betweenness)...")
    betweenness = nx.betweenness_centrality(G, normalized=True)

    # Filtrar apenas deputados (tipo='deputado')
    dep_betweenness = {
        node: score
        for node, score in betweenness.items()
        if G.nodes[node].get("tipo") == "deputado"
    }

    ordenado = sorted(dep_betweenness.items(), key=lambda x: x[1], reverse=True)
    top = ordenado[:top_n]

    print(f"[graph_builder] Top {top_n} 'pontes' identificadas.")
    return top


def get_degree_stats(G: nx.Graph) -> dict:
    """
    Calcula estatísticas de grau do grafo.

    Returns:
        Dicionário com estatísticas básicas.
    """
    degrees = dict(G.degree())
    dep_degrees = {n: d for n, d in degrees.items() if G.nodes[n].get("tipo") == "deputado"}
    frente_degrees = {n: d for n, d in degrees.items() if G.nodes[n].get("tipo") == "frente"}

    return {
        "total_nos": G.number_of_nodes(),
        "total_arestas": G.number_of_edges(),
        "total_deputados": len(dep_degrees),
        "total_frentes": len(frente_degrees),
        "max_frentes_por_dep": max(dep_degrees.values()) if dep_degrees else 0,
        "media_frentes_por_dep": sum(dep_degrees.values()) / len(dep_degrees) if dep_degrees else 0,
        "max_membros_por_frente": max(frente_degrees.values()) if frente_degrees else 0,
    }
