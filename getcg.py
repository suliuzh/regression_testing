import os,csv,json
from pyan.main import mains
import networkx

class getcg(object):
    def __init__(self,path,ignore_dirs):
        self.path = path
        self.pro_name = path.split('/')[-1]
        self.ignore_dirs = ignore_dirs
        self.used = []
        self.getcg()

    def getcg(self):
        filelist=[]
        walk=os.walk(self.path)
        for root, dirs, files in walk:
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            files = [fn for fn in files if os.path.splitext(fn)[1] == ".py"]
            for file_name in files:
                file_name = os.path.join(root, file_name)
                filelist.append(file_name)
        self.used=mains(filelist,self.pro_name)

    def write_to_graph(self):
        G_numpy_mat=networkx.DiGraph()
        with open('dps/'+self.pro_name+'_cg.json','r') as f:
            load_dict = json.load(f)
            for line1,line in load_dict.items():
                for line3 in line:
                    G_numpy_mat.add_node(line1)  #加上文件属性
                    G_numpy_mat.add_node(line3)
                    e=(line1,line3) 
                    G_numpy_mat.add_edge(*e)
        networkx.write_gpickle(G_numpy_mat,'dps/'+self.pro_name+'_graph')
        # print('---------{},{}------'.format(G_numpy_mat.number_of_nodes(),G_numpy_mat.number_of_edges()))

