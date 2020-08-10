import os
import copy
import json
from util import *

import dash
import dash_core_components as dcc
import dash_html_components as html

data_dir = 'masked'
my_username = 'k_xuanlim'

connections = {}
users = [file[:-4] for file in os.listdir(data_dir)]
users_num = len(users)
id_to_name = dict(zip([i for i in range(users_num)], users))
name_to_id = dict(zip(users, [i for i in range(users_num)]))

# get connections
for file in os.listdir(data_dir):
    
    f = open(os.path.join(data_dir, file))
    ls = []
    for line in f:
        ls.append(line.strip())
    f.close()

    username = file[:-4]
    uid = name_to_id[username]
    connections[uid] = []

    shared_friends = set(ls).intersection(users)
    hashed_ff = [name_to_id[friend] for friend in shared_friends]
    connections[uid] = hashed_ff

# param
cluster_no = users_num
merge_threshold = 3
split_threshold = 5

adjacencym = gen_adjacency_matrix(connections)
dist = floyd_warshall(copy.deepcopy(adjacencym), connections)
clusters = kmeans(dist, connections.keys(), cluster_no, merge_threshold, split_threshold)
adjacencym[adjacencym == users_num + 1] = 0

cluster_names = ['cluster ' + str(i + 1) for i in range(len(clusters))]
fig = plot_network(adjacencym, clusters, cluster_names, id_to_name)
fig.show()

res = {}
res['my_username'] = my_username
res['id_to_name'] = id_to_name
res['adjacencym'] = adjacencym.tolist()
res['clusters'] = clusters
res['cluster_names'] = cluster_names

with open('result1.json', 'w') as f:
    json.dump(res, f)


# app = dash.Dash(__name__)

# app.layout = html.Div(children=[
#     dcc.Graph(
#         id='example-graph',
#         figure=plot_network(np.array(res['adjacencym']), 
#             res['clusters'], 
#             res['cluster_names'], 
#             {int(key): value for key, value in res['id_to_name'].items()})
#     )
# ])

# if __name__ == '__main__':
#     app.run_server(debug=True)