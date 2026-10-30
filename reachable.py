import paynt.parser.sketch
import sys
import z3
import infeasible
import time
import random

if len(sys.argv) != 2:
    print("please provide path argument from directory models e.g. thijs/G_Reach")
    sys.exit(1)

filepath = sys.argv[1]
print(f"Path: {filepath}")

SKETCH_PATH = "models/" + filepath + "/sketch.templ"
PROPERTIES_PATH = "models/" + filepath + "/sketch.props"

colored_mdp_factory, task = paynt.parser.sketch.Sketch.load_sketch(
SKETCH_PATH, PROPERTIES_PATH
)

cmdp = colored_mdp_factory.build()
umdp = cmdp.underlying_mdp
n_states = umdp.nr_states
n_parameters = cmdp.parameter_space.num_parameters
options = cmdp.parameter_space.parameter_options
nci = umdp.nondeterministic_choice_indices.copy()
tm = umdp.transition_matrix
cta = cmdp.coloring.getChoiceToAssignment().copy()

log_acc = "\n"

def run_start():
    init = get_init()
    target = get_target()
    reached = set()
    unreachable = set()
    s = z3.Solver()

    bfs_run(reached, init, 1)
    dfs_run(reached, init, target)
    #run_random_traverse(init, target, 10, reached)
    print(f"Reached via preprocessing: {reached}")

    # policy must choose some option per parameter 
    policy = [z3.Int('p_%i' %x) for x in range(n_parameters)]
    s.add(z3.And([z3.Or([policy[i] == options(i)[j] for j in range(len(options(i)))]) for i in range(n_parameters)]))

    # state s is reachable if there is a policy consistent path from init to target trough s
    reachables = [z3.Bool('r_%i' %x) for x in range(n_states)]
    reachability_constraints(s, policy, reachables, init, target)

    time_internal = time.time()
    for c in range(n_states):
      s.push()
      print(f"{c} in reached: {c in reached}")
      if not ((c in reached) or (c in unreachable)):
        s.add(reachables[c])

        if(s.check() == z3.sat):
            print("SAT\n")
            m = s.model()
            for x in range(n_states):
                if m.evaluate(reachables[x], model_completion=True):
                  reached.add(x)
        else:
            print("UN\n")
            unreachable.add(c)
      else:
        print("REACHED\n")
      s.pop()
    print(f"UNREACHABLE: {unreachable}")
    log("time spent in SMT loop: " + str(time.time() - time_internal) + " s\n")

       
def reachability_constraints(s, policy, reachables, init, target):
    parents = create_parents_dict(init)
    s.add(reachables[init])
    s.add(reachables[target])
    
    for state in range(n_states):

      #initial state does not have parents
      if not state == init:
        parent_constraints = []

        for p in parents[state]:
          if cmdp.coloring.getStateToHoles()[p].empty():
            parent_constraints.append(reachables[p] == reachables[state])
          else:
              ass = cta[get_parent_choice(state, p)]

              # If a state is reachable, then at least one of it's parents must be reachable AND the according policy is active (or it has no parents)
              parent_constraints.append(z3.Implies(reachables[state], z3.And([reachables[p]] + [policy[i[0]] == i[1] for i in ass])))

        s.add(z3.Or(parent_constraints))


# Creates a dictionary of state's parents
def create_parents_dict(init):
  parents = {}
  parents.setdefault(init, [])
  for v in range(n_states):
    for choice in range(nci[v], nci[v+1]):
      for edge in tm.get_row(choice):
        # Excludes states to be their own parent (!)
        if not edge.column == v:
          parents.setdefault(edge.column, []).append(v)
  return parents

# Extracts the choice that leads from a state's parent to state
def get_parent_choice(s, p):
   for choice in range(nci[p], nci[p+1]):
      for edge in tm.get_row(choice):
         if edge.column == s:
            return choice

# Extracts a single (!) intial state
def get_init():
  inits = umdp.initial_states
  if len(inits) != 1:
      print(f"RUNTIME WARNING: multiple initial states")      
  return inits[0]

# Extracts a single (!) target state
def get_target():
  targets = []
  for i in range(n_states):
    if 'goal' in umdp.labels_state(i):
      targets.append(i)
  if len(targets) != 1:
    print(f"RUNTIME WARNING: multiple target states")
  return targets[0]


# DEPRICATED
def run_random_traverse(init, target, rep, reached):
  time_traverse = time.time()
  rep_save = rep
  paths = []
  hard_stop = 0
  while (rep > 0):
    print(f"Repetition {rep_save - rep + 1}")
    path = [-1 for x in range(n_parameters)]
    for x in range(n_parameters):
      path[x] = random.randint(0, len(options(x))-1)
    if not path in paths:
      paths.append(path)
      rep -= 1
    else:
      hard_stop += 1
    if (hard_stop > rep_save):
      print("HARD STOP")
      break

    extra_reached = set()
    extra_reached.add(init)
    random_traverse(path,init,extra_reached)

    rev_extra_reached = set()
    rev_extra_reached.add(target)
    rev_random_traverse(path, init, target, rev_extra_reached)

    for r in extra_reached.intersection(rev_extra_reached):
      reached.add(r)
      
  log("random_traverse_time (" + str(rep_save) + " reps): " + str(time.time() - time_traverse) + "s (" + str(len(extra_reached)) + " states reached)\n")
  return

# DEPRICATED
def random_traverse(path, curr, extra_reached):
  for choice in range(nci[curr], nci[curr+1]):
    if easy_consistent_choice(choice, path):
      for r in tm.get_row(choice):
        if not r.column in extra_reached:
          extra_reached.add(r.column)
          random_traverse(path, r.column, extra_reached)

# DEPRICATED
def rev_random_traverse(rev_path, init, curr, rev_extra_reached):
  parents = create_parents_dict(init)
  for p in parents[curr]:
    choice = get_parent_choice(curr, p)
    if easy_consistent_choice(choice, rev_path):
      for r in tm.get_row(choice):
        print(r)
        if not p in rev_extra_reached:
          rev_extra_reached.add(p)
          print(f"added: {p}")
          rev_random_traverse(rev_path, init, p, rev_extra_reached)
    else:
      print("NOT CONSISTENT")
      
#DEPRICATED
def easy_consistent_choice(choice, path):
  t_path = path.copy()
  consistent = True
  if cta[choice]:
    for param, option in cta[choice]:
      if t_path[param] != option:
        consistent = False
  return consistent


def bfs_run(reached, init, depth):
  time_bfs = time.time()
  explored = infeasible.BFS(cmdp, init, depth)
  print(explored)
  for i in range(n_states):
    if explored[i]:
      reached.add(i)
  log("bfs_time (depth " + str(depth) + "): " + str(time.time() - time_bfs) + "s (" + str(sum(explored)) + " states reached)\n")

def dfs_run(reached, init, target):
  time_dfs = time.time()
  pred = infeasible.DFS(cmdp, init, target)
  print([str(i) + ": " + str(x) for i,x in enumerate(pred)])
  c = target
  sum = 0
  while(pred[c] != -1):
    sum += 1
    reached.add(c)
    print(c)
    c = pred[c]
  reached.add(init)
  log("dfs_time: " + str(time.time() - time_dfs) + "s (" + str(sum) + " states reached)\n")

def log(t):
   global log_acc
   log_acc += t
   
def main():
    log("colored MDP: " + str(n_states) + " states, " + str(umdp.nr_choices) + " choices\n")
    log("parameter space: " + str(n_parameters) + " parameters, " + str(cmdp.parameter_space.size) + " possible assignments\n\n")

    time_start_og = time.time()
    run_start()
    log("overall time: " + str((time.time() - time_start_og)) +  "s")

    print(log_acc)
         

if __name__ == "__main__":
    main()


"""

PERSONAL NOTES
- States that can't be reached from init under ANY policy
- States that can't reach the target under ANY policy

Marked: States that are on a policy consistent path from init to target
i.e. states that can be reached from init under policy p and that reach target under policy p
note that the states dashed above can be removed as well, but need SMT computing as well:
remove either
  - s.add(reachables[target])
  - s.add(reachables[init])

"""