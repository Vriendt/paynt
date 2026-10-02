
import paynt.parser.sketch
from collections import deque

""" SKETCH_PATH = "models/thijs/G_Unreach/sketch.templ"
PROPERTIES_PATH = "models/thijs/G_Unreach/sketch.props"

SKETCH_PATH = "models/thijs/G_Reach/sketch.templ"
PROPERTIES_PATH = "models/thijs/G_Reach/sketch.props"
 """

PROJECT_PATH = "models/archive/cav23-saynt/network-2-8-20/"

SKETCH_PATH = PROJECT_PATH + "sketch.templ"
PROPERTIES_PATH = PROJECT_PATH + "sketch.props"

colored_mdp_factory, task = paynt.parser.sketch.Sketch.load_sketch(
    SKETCH_PATH, PROPERTIES_PATH
)

colored_mdp = colored_mdp_factory.build()

""" print(f"colored MDP: {colored_mdp.underlying_mdp.nr_states} states, {colored_mdp.underlying_mdp.nr_choices} choices\n")
print(f"parameter space ({colored_mdp.parameter_space.num_parameters} parameters, {colored_mdp.parameter_space.size} possible assignments):")
print(f"{colored_mdp.parameter_space}\n")


coloring = colored_mdp.coloring
coloring_assignments = coloring.getChoiceToAssignment()
print(f"coloring:\n {coloring_assignments}\n")
print(f"translated coloring for choice 1: {[colored_mdp.parameter_space.parameter_options_to_string(param, [option]) for param, option in coloring_assignments[1]]}")

print(f"\n\n\nThe initial states: {colored_mdp.underlying_mdp.initial_states}\n\n\n")
states = colored_mdp.underlying_mdp.states
for action in states[1].actions:
  print(action)

tm = colored_mdp.underlying_mdp.transition_matrix
v = tm.get_row(1)
for d in v :
  print(f"target state: {d.column}")
  print(f"probability: {d.value()}")
"""

umdp = colored_mdp.underlying_mdp
nci = colored_mdp.underlying_mdp.nondeterministic_choice_indices.copy()
tm = umdp.transition_matrix
coloring_assignments = colored_mdp.coloring.getChoiceToAssignment()
n_parameters = colored_mdp.parameter_space.num_parameters

for state in range(colored_mdp.underlying_mdp.nr_states):
  for choice in range(nci[state], nci[state+1]):
    print(f"state: {state}, choice {choice}: {tm.get_row(choice)}, coloring: {[colored_mdp.parameter_space.parameter_options_to_string(param, [option]) for param, option in coloring_assignments[choice]]}")
  print()


def BFS(s):
  #initialization
  q = deque()
  explored = [False for i in range(umdp.nr_states)]
  path = [-1 for x in range(n_parameters)]
  #print(f"path: {path}")
  q.append((s,path))
  explored[s] = True
  paramex = [] 

  # add unexplored vertices u adjacent to v to queue until empty
  while(q):
    print(f"sum: {sum(explored)} q: {len(q)}")
    
    if(all(explored)):
      break
    v,path = q.popleft()
    #print(f"---------------\ndequeued vertex: {v}, path: {path}\n---------------")
    #print(len(paramex))
    for choice in range(nci[v], nci[v+1]):
      #print(f"choice: {choice}")
      consistent, c_path = consistent_choice(choice, path)
      if (consistent):
        for edge in tm.get_row(choice):
            #print(f"edge to vertex: {edge.column} with prob. {edge.value()}")
            #if not explored[edge.column]:
            if not (edge.column, tuple(c_path)) in paramex:
              #print(f"appending: {edge.column} with {c_path}" )
              q.append(((edge.column), c_path))
              paramex.append((edge.column, tuple(c_path)))
              explored[edge.column] = True
      #print()
    #print()

          

  return explored

def consistent_choice(choice, path):
  t_path = path.copy()
  #print(f"coloring: {coloring_assignments[choice]}")
  #print(f"t_path: {t_path}")
  consistent = True
  if coloring_assignments[choice]:
    for param, option in coloring_assignments[choice]:
      if t_path[param] == -1:
        t_path[param] = option
      if t_path[param] != option:
        consistent = False
  #print(f"consistent: {consistent} by {t_path}")
  return (consistent, t_path)

res = BFS(0)
print(res)
print(all(res))
c = 0
for i in res:
  if not i:
    print(f"vertex {c} is not visited")
  c = c + 1


print(f"colored MDP: {colored_mdp.underlying_mdp.nr_states} states, {colored_mdp.underlying_mdp.nr_choices} choices\n")

print(dir(colored_mdp))
print(len(colored_mdp.coloring.getChoiceToAssignment()))
