# A custom coloring of the maze that colors only some states; the choices of the other states are always enabled, and the best of them is played.
# Two cells play the same move, and the right column plays up below the row H and left from H on.
import payntbind
import stormpy
import z3

import paynt.colored_mdp
import paynt.dt._utils
import paynt.model.model_builder
import paynt.parameter_space.parameter_space
import paynt.synthesizer.synthesizer
import paynt.task
from paynt.utils.coloring_builder import ColoringBuilder

#MODEL_PATH = "models/tests/dt-maze/sketch.templ"
#PROPS_PATH = "models/tests/dt-maze/sketch.props"
MODEL_PATH = "models/thijs/C_Reach/sketch.templ"
PROPS_PATH = "models/thijs/C_Reach/sketch.props"
SAME_MOVE = [(0, 0), (0, 1)]  # (x, y) of the two cells that play the same move
SAME_MOVE_IMP = [(0, 0), (0, 1), (1, 1)]
#COLUMN = 4  # the column that plays up below the row H and left from H on

program = stormpy.parse_prism_program(MODEL_PATH, prism_compatibility=True)
properties = stormpy.parse_properties(open(PROPS_PATH).read(), program)
task = paynt.task.SynthesisTask(properties)
mdp = paynt.model.model_builder.ModelBuilder.from_prism(program, task.specification)

# the choices of state s are row_groups[s], ..., row_groups[s + 1] - 1
row_groups = mdp.nondeterministic_choice_indices
# the values of the model's variables in every state, and the action (an index into action_labels) of every choice
variable_names, valuations = paynt.dt._utils.get_state_valuations(mdp)
print(f"var_names:\n {variable_names}")
print(f"vals:\n {valuations}")
action_labels, choice_to_action = payntbind.synthesis.extractActionLabels(mdp)
print(f"act_lab:\n {action_labels}")
print(f"choice_to_act:\n {choice_to_action}")
moves = ["up", "right", "down", "left"]

# the parameters and their options; in the formulas a parameter's value is the index of its option
space = paynt.parameter_space.parameter_space.ParameterSpace()
space.add_parameter("same", moves)
#space.add_parameter("H", ["0", "1", "2", "3", "4"])

# the builder collects the colors of the choices of this MDP; it needs only the number of parameters, not the space itself
builder = ColoringBuilder(row_groups, space.num_parameters)
# one z3 integer variable per parameter, to write the colors with
#same, H = builder.parameters
same = builder.parameters[0]
# A data column gives a value to every state (state_column) or to every choice (choice_column). In a color it stands for the value of the state or the
# choice whose color is being evaluated, so one formula can color the choices of many states: here y is the row of the choice's state, and move is the
# index of the choice's move in moves (-1 for the other actions).
y = builder.state_column([valuation[variable_names.index("y")] for valuation in valuations])
move = builder.choice_column([moves.index(action_labels[action]) if action_labels[action] in moves else -1 for action in choice_to_action])

# A template is a formula over the parameters and the data columns, translated once; color() then attaches it to any number of choices. A choice is enabled
# under an assignment of the parameters iff its template holds there, with the data of that choice and its state.
same_move = builder.template(move == same)
#up_then_left = builder.template(z3.Or(z3.And(y < H, move == moves.index("up")), z3.And(y >= H, move == moves.index("left"))))
for state in range(mdp.nr_states):
    print(f"\nState {state}")
    position = (valuations[state][variable_names.index("x")], valuations[state][variable_names.index("y")])
    print(position)
    choices = range(row_groups[state], row_groups[state + 1])
    print(choices)
    if len(choices) == 1:
        continue
    # a choice that is not colored is always enabled
    if position in SAME_MOVE:
        builder.color(choices, same_move)
        print("YES")
    #elif position[0] == COLUMN:
        #builder.color(choices, up_then_left)

# every assignment must leave at least one choice in every state (complete=True would ask for exactly one)
builder.check_definition(space, complete=False)
# build() gives PAYNT's standard coloring if every color is a plain (parameter == option) conjunction, and a general coloring otherwise, as here
coloring = builder.build(space)
colored_mdp = paynt.colored_mdp.ColoredMdp(mdp, space, coloring)

result = paynt.synthesizer.synthesizer.Synthesizer.for_method(colored_mdp, task, "smpmc").run()
print(f"best: {result.assignment}, expected steps {result.value}")
