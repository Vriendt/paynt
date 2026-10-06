import paynt.parser.sketch
from collections import deque
import sys

def BFS(colored_mdp, s):
  nci = colored_mdp.underlying_mdp.nondeterministic_choice_indices.copy()
  #init
  q = deque()
  explored = [False for i in range(colored_mdp.underlying_mdp.nr_states)]
  path = [-1 for x in range(colored_mdp.parameter_space.num_parameters)]
  q.append((s,path))
  explored[s] = True

  # key = vertex, value = list of paths leading to vertex
  paramex = {} 

  # main loop: consider unexplored vertex-path combinations until queue is empty or all vertices are explored
  while(q):
    #if(all(explored)):
    #  break
    
    v,path = q.popleft()
    print(f"---------------\ndequeued vertex: {v}, path: {path[18:]}\n---------------")

    # choice from vertex must be consistent with path
    for choice in range(nci[v], nci[v+1]):
      consistent, c_path = consistent_choice(colored_mdp, choice, path)
      if (consistent):
        for edge in colored_mdp.underlying_mdp.transition_matrix.get_row(choice):
            u = edge.column
            if u in paramex:
              # keep the list of paths to vertex u unique under subsetequality
              if not subseteq(tuple(c_path),paramex[u]):
                q.append(((u), c_path))
                paramex[u].append(tuple(c_path))
                explored[u] = True
            else:
               q.append(((u), c_path))
               paramex.update({u : [tuple(c_path)]})
               explored[u] = True
  return explored

def consistent_choice(colored_mdp, choice, path):
  coloring = colored_mdp.coloring.getChoiceToAssignment()
  t_path = path.copy()
  consistent = True
  if coloring[choice]:
    for param, option in coloring[choice]:
      if t_path[param] == -1:
        t_path[param] = option
      if t_path[param] != option:
        consistent = False
  return (consistent, t_path)

def subseteq(curr, ls):
  for l in ls:
    ssq = True
    for i in range(len(curr)):
      if l[i] != -1: #skip all uninits
        if l[i] != curr[i]:
          ssq = False
    if ssq:
      return True
  return False

def main():
    if len(sys.argv) != 2:
        print("provide path argument from directory models e.g. thijs/G_Reach")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"Path: {filepath}")

    SKETCH_PATH = "models/" + filepath + "/sketch.templ"
    PROPERTIES_PATH = "models/" + filepath + "/sketch.props"

    colored_mdp_factory, task = paynt.parser.sketch.Sketch.load_sketch(
    SKETCH_PATH, PROPERTIES_PATH
    )

    colored_mdp = colored_mdp_factory.build()

    print(f"colored MDP: {colored_mdp.underlying_mdp.nr_states} states, {colored_mdp.underlying_mdp.nr_choices} choices\n")
    print(f"parameter space ({colored_mdp.parameter_space.num_parameters} parameters, {colored_mdp.parameter_space.size} possible assignments):")

    coloring_assignments = colored_mdp.coloring.getChoiceToAssignment()
    print(f"translated coloring for choice 1: {[colored_mdp.parameter_space.parameter_options_to_string(param, [option]) for param, option in coloring_assignments[1]]}")

    res = BFS(colored_mdp, 0)
    print(f"\n-----------\nConclusion\n-----------\nall vertices reached: {all(res)}")
    print(f"unvisited vertices: {[i for i,r in enumerate(res) if not r]}")

if __name__ == "__main__":
    main()
