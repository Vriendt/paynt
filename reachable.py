import paynt.parser.sketch
import sys
import z3
from collections import deque
import infeasible
import time
import random

log_acc = "\n"


def run_start(cmdp, target):
    n_states = cmdp.underlying_mdp.nr_states
    n_parameters = cmdp.parameter_space.num_parameters
    options = cmdp.parameter_space.parameter_options
    init = get_init(cmdp)

    reached = set()
    unreachable = set()
    s = z3.Solver()

    #bfs_run(cmdp, n_states, reached, init, 1)
    #run_random_traverse(cmdp, options, reached, 1, n_parameters)

    policy = [z3.Int('p_%i' %x) for x in range(n_parameters)]
    s.add(z3.And([z3.Or([policy[i] == options(i)[j] for j in range(len(options(i)))]) for i in range(n_parameters)]))

    reachables = [z3.Bool('r_%i' %x) for x in range(n_states)]
    indegree_constraints(cmdp, s, policy, reachables, n_states, init)

  
    time_internal = time.time()
    for c in range(n_states):
      print(f"considering state {c}:")
      s.push()
      print(f"{c} in reached: {c in reached}")
      if not ((c in reached) or (c in unreachable)):
        s.add(reachables[c])
        s.add(reachables[init])
        s.add(reachables[target])

        if(s.check() == z3.sat):
            print("SAT\n")
            m = s.model()
            for x in range(n_states):
                #print(f"r{x}: {m.evaluate(reachables[x])}")
                if m.evaluate(reachables[x], model_completion=True):
                  reached.add(x)
            #for p in range(n_parameters):
               #print(f"p{p}: {m.evaluate(policy[p])}")
        else:
            print("UN\n")
            unreachable.add(c)
      else:
        print("REACHED\n")
      s.pop()
    print(f"UNREACHABLE: {unreachable}")
    log("time spent in SMT loop: " + str(time.time() - time_internal) + " s\n")

       
def indegree_constraints(cmdp, s, policy, reachables, n_states, init):
    
    nci = cmdp.underlying_mdp.nondeterministic_choice_indices.copy()
    tm = cmdp.underlying_mdp.transition_matrix
    cta = cmdp.coloring.getChoiceToAssignment()

    parents = create_parents_dict(tm, nci, n_states)
    
    for state in range(n_states):

      #initial state does not have parents
      if not state == init:
        print(state)
        parent_constraints = []

        for p in parents[state]:
          if cmdp.coloring.getStateToHoles()[p].empty():
            parent_constraints.append(reachables[p] == reachables[state])
          else:
              ass = get_parent_params(state, p, nci, tm, cta)

              # If a state is reachable, then at least one of it's parents must be reachable AND the according policy is active (or it has no parents)
              parent_constraints.append(z3.Implies(reachables[state], z3.And([reachables[p]] + [policy[i[0]] == i[1] for i in ass])))

        s.add(z3.Or(parent_constraints))
        #print(z3.Or(parent_constraints))

    
def create_parents_dict(tm, nci, n_states):
  parents = {}
  for v in range(n_states):
    for choice in range(nci[v], nci[v+1]):
      for edge in tm.get_row(choice):
        if not edge.column == v:
          parents.setdefault(edge.column, []).append(v)
  return parents


def get_parent_params(s, p, nci, tm, cta):
   for choice in range(nci[p], nci[p+1]):
      for edge in tm.get_row(choice):
         if edge.column == s:
            return cta[choice]


def get_init(cmdp):
  inits = cmdp.underlying_mdp.initial_states
  if len(inits) == 1:
      init = inits[0]
      print(f"initial state: {init}")
  else:
      print(f"RUNTIME WARNING: multiple initial states")
  return init


def run_random_traverse(cmdp, options, reached, rep, n_parameters):
  rep_save = rep
  time_traverse = time.time()
  paths = []
  while (rep > 0):
    path = [-1 for x in range(n_parameters)]
    for x in range(n_parameters):
      path[x] = random.randint(0, len(options(x))-1)
    if not path in paths:
      print(f"{path}\n\n")
      paths.append(path)
      rep -= 1
    curr = get_init(cmdp)
    extra_reached = set()
    extra_reached.add(curr)
    random_traverse(cmdp,path,curr,extra_reached)
  for i in extra_reached:
    reached.add(i)
  log("random_traverse_time (" + str(rep_save) + " reps): " + str(time.time() - time_traverse) + "s (" + str(len(extra_reached)) + " states reached)\n")


def random_traverse(cmdp, path, curr, extra_reached):
  nci = cmdp.underlying_mdp.nondeterministic_choice_indices.copy()
  tm = cmdp.underlying_mdp.transition_matrix
  for choice in range(nci[curr], nci[curr+1]):
    if easy_consistent_choice(cmdp, choice, path):
      for r in tm.get_row(choice):
        if not r.column in extra_reached:
          extra_reached.add(r.column)
          random_traverse(cmdp,path, r.column, extra_reached)


def easy_consistent_choice(colored_mdp, choice, path):
  coloring = colored_mdp.coloring.getChoiceToAssignment()
  t_path = path.copy()
  consistent = True
  if coloring[choice]:
    for param, option in coloring[choice]:
      if t_path[param] != option:
        consistent = False
  return consistent


def bfs_run(cmdp, n_states, reached, init, depth):
  time_bfs = time.time()
  explored = infeasible.BFS(cmdp, init, depth)
  print(explored)
  for i in range(n_states):
    if explored[i]:
      reached.add(i)
  log("bfs_time (depth " + str(depth) + "): " + str(time.time() - time_bfs) + "s (" + str(sum(explored)) + " states reached)\n")

def log(t):
   global log_acc
   log_acc += t
   
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

    cmdp = colored_mdp_factory.build()
    n_states = cmdp.underlying_mdp.nr_states

    log("colored MDP: " + str(cmdp.underlying_mdp.nr_states) + " states, " + str(cmdp.underlying_mdp.nr_choices) + " choices\n")
    log("parameter space: " + str(cmdp.parameter_space.num_parameters) + " parameters, " + str(cmdp.parameter_space.size) + " possible assignments\n\n")

    time_start_og = time.time()
    run_start(cmdp, n_states - 1)

    log("overall time: " + str((time.time() - time_start_og)) +  "s")
    print(log_acc)

    """
    for i in range(n_states):
       if cmdp.underlying_mdp.labels_state(i) == {'goal'}:
          print(i)
    """
          
if __name__ == "__main__":
    main()


"""
without BFS:
internal_time: 118.45492887496948 s
overall time: 137.50816416740417 s

DEPTH 10
bfs_time: 6.198304176330566 s (1387 states reached)
internal_time: 94.04672312736511 s
overall time: 119.40677905082703 s

with BF depth 20:
bfs_time: 6.363090991973877 s (1389 states reached)
internal_time: 107.72586393356323 s
overall time: 132.8140058517456 s

with BF depth 30:
bfs_time: 10.249868154525757 s
internal_time: 106.91810297966003 s
overall time: 135.78085207939148 s

with BF depth 50:
bfs_time: 18.358196020126343 s (1389 states reached)
internal_time: 108.2756359577179 s
overall time: 145.32890915870667 s

with a single traverse (some 3K states reached): check if this is correct?
internal_time: 73.67181897163391 s
overall time: 98.87716817855835 s
"""