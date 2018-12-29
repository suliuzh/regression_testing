import ast,os
import operator
import numpy


class node_def(object):
    def __init__(self,typen,namen,linen,filen='',namespace='',):
        self.typen=typen
        self.namen=namen
        self.linen=linen
        self.namespace=namespace
        self.filen=filen  
    def print_node(self):
        return [ value for name,value in vars(self).items()]
        #return (','.join([ str(value) for name,value in vars(self).items()]))
    def get_name(self):
        return ('.'.join([self.namespace,self.namen]))

def module_name(filename):
    return filename.split('/')[-1].strip('.py')
class xxx(ast.NodeVisitor):
    def __init__(self,filenames):
        self.defs={}
        self.filen=''
        self.filenames=filenames
        self.namespace={}
        self.process()
    def process(self):
        for file_name in self.filenames:
            self.filen=file_name
            with open(file_name, "rt", encoding="utf-8") as f:
                content = f.read()
            try:
                ast_nodes=ast.parse(content, file_name)
                #print(module_name(file_name))
                for node in ast_nodes.body:
                    if isinstance(node,ast.FunctionDef):
                        self.visit_FunctionDef(node,module_name(file_name))
                    elif isinstance(node,ast.ClassDef):
                        self.visit_ClassDef(node,module_name(file_name))
            except:
                return
    def visit_ClassDef(self, node,ns):
        name=node.name
        linedef=node.lineno
        temp=node_def('class',name,linedef,self.filen,ns)
        if name not in self.defs.keys():
            self.defs[name]=[temp]
        else:
            self.defs[name].append(temp)
        self.namespace[name]=ns
        ns=ns+'.'+name 
        for stmt in node.body:
            if isinstance(stmt,ast.FunctionDef):
                self.visit_FunctionDef(stmt,ns)
            elif isinstance(stmt,ast.ClassDef):
                self.visit_ClassDef(stmt,ns)
    def visit_FunctionDef(self, node,ns):
        name=node.name
        linedef=node.lineno
        temp=node_def('function',name,linedef,self.filen,ns)
        if name not in self.defs.keys():
            self.defs[name]=[temp]
        else:
            self.defs[name].append(temp)
        self.namespace[name]=ns 
        ns=ns+'.'+name
        for stmt in node.body:
            if isinstance(stmt,ast.FunctionDef):
                self.visit_FunctionDef(stmt,ns)
            elif isinstance(stmt,ast.ClassDef):
                self.visit_ClassDef(stmt,ns)
def analyse_file_api(filenames):
    a=xxx(filenames)
    funcs_list=[]
    for k,v in a.defs.items():
        for item in v:
            funcs_list.append([item.get_name(),item.linen])
    funcs_list.sort(key=operator.itemgetter(1))
    return funcs_list