# regression_testing
软件分析与测试实验
这是一个回归测试工具，使用方法如下：
it is a tool of impact analysis for regression testing
optional arguments:
-h, --help show this help message and exit
-l list the callgraph of exist projects
-g G generate the callgraph of the provided project
-p P provide the name of the project and start analysis
-cm CM please imput the commit sha
用户在使用过程中,首先需要将项目源代码克隆到 projects 文件夹下,然后调用-g 参数生
成项目调用图,然后调用-p 参数指定项目名称,-cm 参数指定版本号,如 commit sha,进
行分析。

