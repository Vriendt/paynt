import paynt.parser.sketch
from collections import deque
import sys

def BFS(colored_mdp, s):
  nci = colored_mdp.underlying_mdp.nondeterministic_choice_indices.copy()
  #initialization
  q = deque()
  explored = [False for i in range(colored_mdp.underlying_mdp.nr_states)]
  path = [-1 for x in range(colored_mdp.parameter_space.num_parameters)]
  #print(f"path: {path}")
  q.append((s,path))
  explored[s] = True
  paramex = [] 

  # add unexplored vertices u adjacent to v to queue until empty
  while(q):
    #print(f"sum: {sum(explored)} q: {len(q)}")

    """
    if(all(explored)):
      break
    """
    v,path = q.popleft()
    print(f"---------------\ndequeued vertex: {v}, path: {path[18:]}\n---------------")
    #print(len(paramex))
    for choice in range(nci[v], nci[v+1]):
      #print(f"choice: {choice}")
      consistent, c_path = consistent_choice(colored_mdp, choice, path)
      if (consistent):
        for edge in colored_mdp.underlying_mdp.transition_matrix.get_row(choice):
            #print(f"edge to vertex: {edge.column} with prob. {edge.value()}")
            #if not explored[edge.column]:
            u = edge.column
            if not (u, tuple(c_path)) in paramex:
              print(f"appending: {edge.column} with {c_path[18:]}" )
              q.append(((u), c_path))
              paramex.append((u, tuple(c_path)))
              explored[u] = True
            else:
               print(f"\nPrevented {u} with {c_path[18:]}\n")
      #print()
      else:
         print(f"Filtered inconsistent: {choice} with {path}")
    #print()
  print(f"paramex length: {len(paramex)}")
  return explored

def consistent_choice(colored_mdp, choice, path):
  coloring = colored_mdp.coloring.getChoiceToAssignment()
  t_path = path.copy()
  #print(f"coloring: {coloring[choice]}\n t_path: {t_path}")
  consistent = True
  if coloring[choice]:
    for param, option in coloring[choice]:
      if t_path[param] == -1:
        t_path[param] = option
      if t_path[param] != option:
        consistent = False
  #print(f"consistent: {consistent} by {t_path}")
  return (consistent, t_path)


#TODO: add cl param: "verbose" (options: full, minimal, none)

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



# In reach, there is are vertices that are not reachable, because of coloring, why is this vertex created, 
# and is there a way in which to predict that those unreachable created vertices will be created, due to coloring?


# In words: once you have reached a vertex v per path p, then we don't want to revisit v per extension p' of path p
# in other words subset: think about a good way to chef this
# path_eq = comparison of tuples t (in queue) and r (new):
#             if t[x] = -1 or t[x] == r[x]:
                  #continue
              # else: r is actually new and must be appended to queue.