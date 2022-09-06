import argparse
import pandas as pd
from sklearn import decomposition
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.neighbors import DistanceMetric
import csv

parser = argparse.ArgumentParser("Contribution Space")
parser.add_argument("summary_file", help="The path of the csv summary file to be parsed.", type=str)
parser.add_argument("sources", help="The source populations comma separated", type=str)
args = parser.parse_args()

targets = []
vectors = []
out_lines = []

df = pd.read_csv(args.summary_file, skiprows=0)
NUM_OF_SOURCES = len(args.sources.split(','))
SOURCES = args.sources.split(',')

for i in range(len(df)):
    target = df.iloc[i].iloc[0]
    vec = []
    try:
        for s in range(NUM_OF_SOURCES):
            element = float(df.iloc[i].iloc[s + 1].split(', ')[-1])
            vec.append(element)
        targets.append(target)
    except:
        continue

    vectors.append(vec)
    out_lines.append(df.iloc[i])


X = vectors
y = targets

pca = decomposition.PCA(n_components=3)
pca.fit(X)
X = pca.transform(X)

fig = px.scatter_3d(
    X, x=0, y=1, z=2, color=targets)

fig.show()

# computing clusters, the selected clusters maximize the average distance between the clusters' centers
clusters_max = None
max_dist = 0
dist_metric = DistanceMetric.get_metric('euclidean')

for i in range(2, len(vectors)):
    kmeans = KMeans(n_clusters=i, random_state=0).fit(X)
    centers = kmeans.cluster_centers_
    dists = []
    for c1 in centers:
        for c2 in centers:
            if (c1 != c2).all():
                dists.append(dist_metric.pairwise([list(c1)], [list(c2)]))
    average_dists = sum(dists) / len(dists)
    if average_dists > max_dist:
        max_dist = average_dists
        clusters_max = kmeans.labels_

print('Number of clusters: ' + str(len(set(clusters_max))))

for i in range(len(vectors)):
    print(str(targets[i]) + ' is in cluster number ' + str(clusters_max[i]))

fout = open("Clusters" + ".csv", "a")
write_outfile = csv.writer(fout)
columns = ['cluster'] + ['target'] + SOURCES
write_outfile.writerow(columns)
c_t = list(zip(clusters_max, targets))
c_t.sort(key=lambda t: t[0])

for cn, target in c_t:
    for line in out_lines:
        line_ = []
        if line.iloc[0] == target:
            for k in range(len(SOURCES)+1):
                line_.append(line.iloc[k])
            write_outfile.writerow([str(cn)] + line_)

fout.close()

clusters_csv = pd.read_csv("Clusters.csv")

def _color_cell(c):
    try:
        if len(c.split(' ')) > 1:
            val = float(c.split(' ')[-1])
            if val >= 0.25:
                return 'background-color: green'
            if val <= -0.25:
                return 'background-color: red'
            return 'background-color: yellow'
        else:
            return ''
    except:
        return ''


clusters_csv.style.applymap(_color_cell).to_excel('Clusters_Colored.xlsx', index=False, engine='openpyxl')
