import graphviz

dot = graphviz.Digraph(comment='The Round Table')

dot.node('0', 'King Arthur')
dot.node('1', 'Sir Bedevere the Wise')
dot.node('2', 'Sir Lancelot the Brave')

dot.edges(['01', '02'])
dot.edge('B', 'L', constraint='false')
print(dot.source)

dot.render('round-table.gv', view=True, format='png')