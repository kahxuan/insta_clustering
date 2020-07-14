import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go

def gen_adjacency_matrix(connections):
    user_num = len(connections.keys())
    matrix = np.zeros((user_num, user_num), dtype='int64')
    matrix += user_num + 1
    for fid in connections.keys():
        matrix[fid][fid] = 0
        for ffid in connections[fid]:
            matrix[fid][ffid] = 1
    return matrix


def floyd_warshall(dist, connections):
    n = dist.shape[0]
    for k in range(n):
        for u in range(n):
            for v in range(n):
                dist[u][v] = min(dist[u][v], dist[u][k] + dist[k][v])
    return dist


def assign_cluster(node, centroids, dist):
    min_centroids, min_dist = 0, dist[centroids[0]][node]
    for i in range(1, len(centroids)):
        if dist[node][centroids[i]] < min_dist:
            min_centroids = i
            min_dist = dist[centroids[i]][node]
    return min_centroids


def form_clusters(centroids, node_list, dist):
    clusters = [[] for i in range(len(centroids))]
    for node in node_list:
        i = assign_cluster(node, centroids, dist)
        clusters[i].append(node)
    return clusters


def get_cluster_dist(dist, cluster):
    cluster_dist = np.take(dist, cluster, axis=0)
    cluster_dist = np.take(cluster_dist, cluster, axis=1)
    return cluster_dist


def get_centroids(clusters, dist):
    centroids = [0] * len(clusters)
    for i, cluster in enumerate(clusters):
        cluster_dist = get_cluster_dist(dist, cluster)
        dist_sum = cluster_dist.sum(axis=1)
        centroids[i] = cluster[np.where(dist_sum == min(dist_sum))[0][0]]
    return centroids


def get_loss(clusters, centroids, dist):
    loss = 0
    for i in range(len(centroids)):        
        loss += sum(np.take(dist[centroids[i], :], clusters[i])) / (len(clusters[i]) / 1.5)
    return loss


def merge_clusters(clusters, centroids, dist, threshold=3):
    for i in range(len(centroids)):
        for j in range(i + 1, len(centroids)):
            if dist[centroids[i]][centroids[j]] <= threshold:
                centroids.pop(j)
                clusters[i] += clusters.pop(j)
                return clusters, centroids, True
    return clusters, centroids, False


def converge(centroids, node_list, dist):
    for _ in range(3):
        clusters = form_clusters(centroids, node_list, dist)
        centroids = get_centroids(clusters, dist)
    return clusters, centroids


def split_cluster(centroids, clusters, dist, threshold=5):
    for i, cluster in enumerate(clusters):
        cluster_dist = get_cluster_dist(dist, cluster)
        row, col = np.unravel_index(cluster_dist.argmax(), cluster_dist.shape)
        if cluster_dist[row, col] >= threshold:
            centroids.pop(i)
            centroids.append(cluster[row])
            centroids.append(cluster[col])
            return centroids, True
    return centroids, False


def kmeans(dist, node_list, cluster_no, merge_threshold, split_threshold):
    centroids = np.random.choice(np.array(list(node_list)), size=cluster_no, replace=False)
    clusters, centroids = converge(centroids, node_list, dist)
    
    clusters, centroids, merged = merge_clusters(clusters, centroids, dist, merge_threshold)
    clusters, centroids = converge(centroids, node_list, dist)
    centroids, split = split_cluster(centroids, clusters, dist, split_threshold)
    clusters, centroids = converge(centroids, node_list, dist)
    
    op_loss = get_loss(clusters, centroids, dist)
    op_clusters = clusters
    
    for i in range(100):
        
        if not split and not merged:
            return op_clusters
        
        clusters, centroids, merged = merge_clusters(clusters, centroids, dist, merge_threshold)
        clusters, centroids = converge(centroids, node_list, dist)
        
        centroids, split = split_cluster(centroids, clusters, dist, split_threshold)
        clusters, centroids = converge(centroids, node_list, dist)
        
        cur_loss = get_loss(clusters, centroids, dist)
        if cur_loss < op_loss:
            op_loss = cur_loss
            op_clusters = clusters

    return clusters


def plot_network(adjacencym, clusters, legend_names, id_to_name, my_username):

    traces = []
    G = nx.from_numpy_matrix(adjacencym) 
    pos = nx.spring_layout(G)
    
    # edge trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.3, color='rgba(190, 190, 190, 0.5)'),
        hoverinfo='none',
        mode='lines',
        name='connection')

    traces.append(edge_trace)
    
    # node traces
    for i, cluster in enumerate(clusters):
        node_x = []
        node_y = []
        for node in cluster:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

        node_trace = go.Scatter(
            x=node_x, 
            y=node_y,
            mode='markers',
            text=[id_to_name[uid] for uid in cluster],
            hovertemplate='%{text}<br>(' + legend_names[i] + ')<extra></extra>',
            marker=dict(
                # color='rgb' + str(tuple(np.random.randint(1, 255, size=3))),
                colorscale='YlGnBu',
                size=7), 
            name=legend_names[i])

        traces.append(node_trace)
    
    # create figure
    fig = go.Figure(data=traces,
             layout=go.Layout(
                title=my_username + "'s Instagram Network",
                titlefont_size=16,
                hovermode='closest',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

    fig.update_layout(plot_bgcolor='#ffffff')
    
    fig.show()