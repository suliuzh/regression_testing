#以影响文件为关键词找到该文件的commit
from git import Repo
import networkx
import logging,re,os,csv,time
import numpy
from getcg import getcg
from diff_parser import parse_diff
from getapi import analyse_file_api
import json
import argparse
import logging
import matplotlib.pyplot as plt


class Regression(object):
    def __init__(self,G,path,cm_sha,logger):
        self.G = G
        self.cm_sha=cm_sha
        self.path = path
        self.changed_apis = {}   #这是更改的模块（粒度为函数或方法）
        self.impact_nodes={}     #影响的模块
        self.logger = logger

    def changeget(self,git):
        diff=git.diff(self.cm_sha,self.cm_sha+'^')
        cm_info=parse_diff(diff)
        files_list=set()
        flag_py = 0
        flag_cm_py = 0
        for item in cm_info:
            if(item.src_file.endswith('.py')):
                flag_cm_py = 1
                true_path=path+'/'+item.src_file
                if os.path.exists(true_path):
                    flag_py = 1
                    f= open(true_path,'r',encoding='utf-8')
                    contents=f.readlines()
                    file_apis=analyse_file_api([true_path])
                    add_apis_lins=item.hunk_infos['a']
                    if file_apis:
                        for api_lin in add_apis_lins:
                            if file_apis[-1][1]< api_lin:#如果最后一个范围之内，则认为是该API
                                self.changed_apis[file_apis[-1][0]] = true_path
                                continue
                            for i,api in enumerate(file_apis):
                                if api[1] > api_lin:
                                    if (file_apis[i-1])[1]<= api_lin:
                                        self.changed_apis[file_apis[i-1][0]]=true_path   
                                    else:
                                        break

        git.reset('--hard',self.cm_sha+'~1')   #回退上一版本
        for item in cm_info:
            if(item.src_file.endswith('.py')):
                flag_cm_py = 1
                true_path=self.path+'/'+item.src_file
                if os.path.exists(true_path):
                    flag_py = 1
                    files_list.add(true_path)
                    f= open(true_path,'r',encoding='utf-8')
                    contents=f.readlines()
                    file_apis=analyse_file_api([true_path])
                    delete_apis_lins=item.hunk_infos['d']
                    if file_apis:
                        for api_lin in delete_apis_lins:
                            if file_apis[-1][1]< api_lin:#如果最后一个范围之内，则认为是该API
                                self.changed_apis[file_apis[-1][0]] = true_path
                                continue
                            for i,api in enumerate(file_apis):
                                if api[1] == api_lin:
                                    #删除了一个API：
                                    self.changed_apis[api[0]] = true_path  
                                    break
                                elif api[1] > api_lin:
                                    if (file_apis[i-1])[1]< api_lin:
                                        self.changed_apis[file_apis[i-1][0]]=true_path   #前一个才是更改的文件
                                    else:
                                        break        
        if self.changed_apis == {}:
            if (flag_cm_py == 0):
                self.logger.warning('this commit doesn''t have .py file')
            elif (flag_py == 0):
                self.logger.warning('dont has all .py in the project in the commit')
            else:
                self.logger.warning('no function or method being in this commit')

    def changeimpactcg(self):
        #更改函数的影响分析
        Nodes=self.G.nodes
        for tem,v in self.changed_apis.items():
            for node in Nodes:
                if node and node.endswith(tem):  #如果找到了
                    for nodef in list(Nodes):
                        if nodef and nodef != node and networkx.has_path(self.G,nodef,node): #其他节点是否有路径到它，间接路径也算
                            if node in self.impact_nodes.keys():
                                self.impact_nodes[node].add(nodef)
                            else:
                                self.impact_nodes[node]=set()
                                self.impact_nodes[node].add(nodef)

       

if __name__ == '__main__':
    #定义命令行参数
    parser = argparse.ArgumentParser(description="it is a tool of impact analysis for regression testing")
    parser.add_argument('-l',help="list the callgraph of exist projects",required=False,action="store_true")
    parser.add_argument('-g',help="generate the callgraph of the provided project",required=False)
    parser.add_argument('-p',help="provide the name of the project and start analysis",required=False)
    parser.add_argument('-cm',help="please imput the commit",required=False)
    args =parser.parse_args()
    logger = logging.getLogger()
    if args.l:
        for file_ in os.listdir('dps/'):
            if file_.endswith('_graph'):
                logger.warning(file_.split('_')[0])
    if args.g:
        name = args.g
        path = 'projects/'+name
        if os.path.exists(path):
            logger.warning('start to generate the callgraph!')
            ignore_dirs = []
            time_start = time.clock()
            getcg_class = getcg(path,ignore_dirs)
            getcg_class.write_to_graph()
            logger.warning('end!')
            time_end = time.clock()
            print('time is',time_end-time_start)
        else:
            logger.warning('wrong!-----you should clone the project——'+name+'in the projects folder')
    if args.p:
        name = args.p
        if os.path.exists('dps/'+name+'_graph'):
            pass
        else:
            logger.warning('wrong!-----you have not generate the  callgraph of any project')

    if args.cm:
        if os.path.exists('dps/'+name+'_graph'):
            G_numpy_mat= networkx.read_gpickle('dps/'+name+'_graph')
            path='projects/'+name
            # plt.figure(figsize=(10,9))
            # pos = networkx.circular_layout(G_numpy_mat)
            # networkx.draw_networkx(G_numpy_mat,pos)
        else:
            logger.warning('wrong!-----you have not generate the callgraph of the project')
            exit()
        cm_sha=args.cm
        repo=Repo(path)
        git=repo.git
        try:  
            git.reset('--hard',cm_sha)
            #获得当前有多少测试文件
            filelist=[]
            ignore_dirs=[]
            walk=os.walk(path)
            for root, dirs, files in walk:
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                files = [fn for fn in files if os.path.splitext(fn)[1] == ".py"]
                for file_name in files:
                    file_name = os.path.join(root, file_name)
                    filelist.append(file_name)
            whole_test=set()
            for n in filelist:
                if n.split('/')[-1].startswith('test_'):
                    whole_test.add(n.strip('.py'))
            logger.warning(len(whole_test))
            re_model = Regression(G_numpy_mat,path,cm_sha,logger)
            re_model.changeget(git)
            re_model.changeimpactcg()
            logger.warning('changed_api:{}'.format(len(re_model.changed_apis)))
            # logger.warning('impact_nodes:'len(re_model.impact_nodes))
            impact_within_nodes=set()
            for k,v in re_model.impact_nodes.items():
                for item in v:
                    if item.split('.')[-1].startswith('test_'):
                        temp = item.split('.')
                        end_temp = []
                        for ins in temp:
                            if ins.startswith('test_'):#第一个test_开头的就应该是文件
                                end_temp.append(ins)
                                end_t = '/home/cyl/Downloads/projects/'+'/'.join(end_temp)
                                # if end_t in whole_test:
                                if '.'.join(end_temp) not in impact_within_nodes:
                                        impact_within_nodes.add('.'.join(end_temp))
                                break
                            else:
                                end_temp.append(ins)
            logger.warning(len(impact_within_nodes))
            json_dict = {}
            json_dict['changed_apis']=list(re_model.changed_apis)
            json_dict['has_impact_apis']=list(re_model.impact_nodes)
            json_dict[cm_sha] = list(impact_within_nodes)
            with open('jsondata/'+name+cm_sha+'.json','w') as f:
                json.dump(json_dict,f,indent=4)
        except Exception:
            logger.warning('wrong!-----you give wrong commit sha or you don not clone the project in the projects folder')