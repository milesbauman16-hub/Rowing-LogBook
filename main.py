from drafter import *
from dataclasses import dataclass

# ---------------------------------------------------------------- state
@dataclass
class Workout:
    category: str      # piece / steady / interval / lift / cross / recovery
    subtype: str       # 2k, 6k, 2x10', Time, Distance, Bike, ...
    date: str
    time: str
    distance: str
    split: str
    rate: str
    avg_hr: str
    max_hr: str
    count: str
    rest: str
    feel: str

@dataclass
class State:
    workouts: list[Workout]     # every logged workout (changed in save_workout)
    piece_types: list[str]      # 2k, 6k, 2x10' + anything made with "Create New"
    last_logged: str            # summary of the most recently saved workout
    last_order: str             # most recent sort order the user picked in a list


# ---------------------------------------------------------------- config
# These are constants (never changed while the program runs), so they are
# allowed as global constants.
LABELS = {
    "date": "Date (YYYY-MM-DD)", "time": "Time", "distance": "Distance",
    "split": "Split (m:ss.s)", "rate": "Rate", "avg_hr": "Avg HR",
    "max_hr": "Max HR", "count": "How many", "rest": "Rest time",
    "feel": "Feel (1-10)",
}

FORM_FIELDS = {
    "piece":    ["date", "time", "split", "rate", "avg_hr", "max_hr"],
    "steady":   ["date", "time", "distance", "split", "rate", "avg_hr", "max_hr"],
    "interval": ["date", "count", "time", "distance", "split", "rest", "rate", "avg_hr", "max_hr"],
    "lift":     ["date", "time", "feel"],
    "cross":    ["date", "distance", "time", "avg_hr", "max_hr"],
    "recovery": ["date", "time"],
}

CATEGORY_TITLES = {
    "piece": "Piece Work", "steady": "Steady State", "interval": "Intervals",
    "lift": "Lifts", "cross": "Cross-Training", "recovery": "Yoga/Recovery",
}

# Sentinel value: to_seconds returns this for text that can't be read as a
# time, so bad splits sort to the end and can be filtered out of graphs.
BAD_TIME = 10**9

# ---------------------------------------------------------------- helpers
def to_seconds(text: str) -> float:
    """'1:45.3' -> 105.3, '30' -> 30.0, bad input -> BAD_TIME (sorts last)."""
    # ADVANCED: try/except catches the ValueError that float() raises when the
    # text isn't a number (like an empty box), so the program doesn't crash.
    try:
        parts = [float(p) for p in text.strip().split(":")]
        total = 0.0
        for p in parts:
            total = total * 60 + p      # minutes -> seconds, hours -> seconds
        return total
    except ValueError:
        return BAD_TIME

def matching(state: State, category: str, subtype: str) -> list[Workout]:
    """All workouts in a category; subtype "" means 'any subtype'."""
    # ADVANCED: list comprehension = a loop that builds a list in one line.
    return [w for w in state.workouts
            if w.category == category and (subtype == "" or w.subtype == subtype)]

def sort_workouts(items: list[Workout], order: str) -> list[Workout]:
    # ADVANCED: sorted(..., key=lambda w: ...) sorts by a value computed from
    # each item. A lambda is a tiny one-line function with no name; here it
    # takes a workout w and returns the thing to sort by.
    if order == "Newest-Oldest":
        return sorted(items, key=lambda w: w.date, reverse=True)
    if order == "Fastest-Slowest":
        return sorted(items, key=lambda w: to_seconds(w.split))
    if order == "Shortest-Longest":
        return sorted(items, key=lambda w: to_seconds(w.time))
    return items

def workout_table(items: list[Workout], category: str):
    cols = FORM_FIELDS[category]
    # Header row: label text with the "(YYYY-MM-DD)" style hints removed.
    rows = [[LABELS[c].split(" (")[0] for c in cols]]
    for w in items:
        # ADVANCED: getattr(w, c) reads an attribute using its name as a
        # string (getattr(w, "split") is the same as w.split). This lets one
        # loop build the columns for every category from FORM_FIELDS.
        rows.append([getattr(w, c) for c in cols])
    return Table(rows)

def back_home():
    return Button("Home", index)

# ---------------------------------------------------------------- home
@route
def index(state: State) -> Page:
    content = [
        Header("Rowing Workout Logbook"),
        Button("Log Workout", log_menu),
        LineBreak(),
    ]
    # Show the two remembered state values once they have been set.
    if state.last_logged != "":
        content.append(Text(f"Last logged: {state.last_logged}"))
    if state.last_order != "":
        content.append(Text(f"Last list order used: {state.last_order}"))
    content += [
        Header("View", 2),
        Button("View Pieces", view_pieces),
        Button("View Steady State", view_steady),
        Button("View Lifts", view_sorted_category, [Argument("category", "lift"), Argument("subtype", "")]),
        Button("View Cross-Training", view_cross),
        Button("View Recovery", view_sorted_category, [Argument("category", "recovery"), Argument("subtype", "")]),
    ]
    return Page(state, content)

# ---------------------------------------------------------------- LOGGING
@route
def log_menu(state: State) -> Page:
    return Page(state, [
        Header("Type of Workout?"),
        Button("Piece Work", log_piece_menu),
        Button("Steady State", log_steady_menu),
        Button("Lift", log_form, [Argument("category", "lift"), Argument("subtype", "Lift")]),
        Button("Cross-Training", log_cross_menu),
        Button("Yoga/Recovery", log_form, [Argument("category", "recovery"), Argument("subtype", "Recovery")]),
        LineBreak(), back_home(),
    ])

@route
def log_piece_menu(state: State) -> Page:
    content = [Header("What type of piece?")]
    for t in state.piece_types:
        content.append(Button(t, log_form, [Argument("category", "piece"), Argument("subtype", t)]))
    content += [Button("Create New", create_piece_type_form), LineBreak(), Button("Back", log_menu)]
    return Page(state, content)

@route
def create_piece_type_form(state: State) -> Page:
    return Page(state, [
        Header("Create a new piece type"),
        TextBox("new_name", ""),
        Button("Create", create_piece_type),
        Button("Back", log_piece_menu),
    ])

@route
def create_piece_type(state: State, new_name: str) -> Page:
    new_name = new_name.strip()
    if new_name and new_name not in state.piece_types:
        state.piece_types.append(new_name)      # modifies state.piece_types
    # ADVANCED: a route is just a function, so we can call another route
    # directly and return the Page it builds.
    return log_piece_menu(state)

@route
def log_steady_menu(state: State) -> Page:
    return Page(state, [
        Header("What type of piece?"),
        Button("Time", log_form, [Argument("category", "steady"), Argument("subtype", "Time")]),
        Button("Distance", log_form, [Argument("category", "steady"), Argument("subtype", "Distance")]),
        Button("Interval", log_interval_menu),
        LineBreak(), Button("Back", log_menu),
    ])

@route
def log_interval_menu(state: State) -> Page:
    return Page(state, [
        Header("Interval type"),
        Button("Interval Time", log_form, [Argument("category", "interval"), Argument("subtype", "Interval Time")]),
        Button("Interval Distance", log_form, [Argument("category", "interval"), Argument("subtype", "Interval Distance")]),
        LineBreak(), Button("Back", log_steady_menu),
    ])

@route
def log_cross_menu(state: State) -> Page:
    return Page(state, [
        Header("Cross-Training"),
        Button("Bike", log_form, [Argument("category", "cross"), Argument("subtype", "Bike")]),
        Button("Swim", log_form, [Argument("category", "cross"), Argument("subtype", "Swim")]),
        Button("Run", log_form, [Argument("category", "cross"), Argument("subtype", "Run")]),
        LineBreak(), Button("Back", log_menu),
    ])

@route
def log_form(state: State, category: str, subtype: str) -> Page:
    content = [Header(f"Log: {subtype}")]
    # Loop over the field names for this category and make one TextBox each.
    # The TextBox name matches a parameter of save_workout.
    for f in FORM_FIELDS[category]:
        content += [Text(LABELS[f]), TextBox(f, ""), LineBreak()]
    content += [
        Button("Save", save_workout, [Argument("category", category), Argument("subtype", subtype)]),
        Button("Cancel", log_menu),
    ]
    return Page(state, content)

# ADVANCED: the "= ''" defaults make these parameters optional. Each category's
# form only has some of the TextBoxes, so the missing ones default to "".
@route
def save_workout(state: State, category: str, subtype: str, date: str = "", time: str = "",
                 distance: str = "", split: str = "", rate: str = "", avg_hr: str = "",
                 max_hr: str = "", count: str = "", rest: str = "", feel: str = "") -> Page:
    state.workouts.append(Workout(category, subtype, date, time, distance, split,
                                  rate, avg_hr, max_hr, count, rest, feel))   # modifies state.workouts
    state.last_logged = f"{subtype} on {date}"                                 # modifies state.last_logged
    return Page(state, [
        Header("Saved!"),
        Button("Log another", log_form, [Argument("category", category), Argument("subtype", subtype)]),
        back_home(),
    ])

# ---------------------------------------------------------------- VIEW: pieces
@route
def view_pieces(state: State) -> Page:
    content = [Header("View Pieces")]
    for t in state.piece_types:
        content.append(Button(f"View {t}", piece_view_mode, [Argument("subtype", t)]))
    content += [LineBreak(), back_home()]
    return Page(state, content)

@route
def piece_view_mode(state: State, subtype: str) -> Page:
    return Page(state, [
        Header(f"{subtype}: how do you want to view it?"),
        Button("View List", piece_list_order, [Argument("subtype", subtype)]),
        Button("Graph View", piece_graph_menu, [Argument("subtype", subtype)]),
        LineBreak(), Button("Back", view_pieces),
    ])

@route
def piece_list_order(state: State, subtype: str) -> Page:
    return Page(state, [
        Header(f"{subtype} list"),
        Button("Newest-Oldest", show_list, [Argument("category", "piece"), Argument("subtype", subtype), Argument("order", "Newest-Oldest")]),
        Button("Fastest-Slowest", show_list, [Argument("category", "piece"), Argument("subtype", subtype), Argument("order", "Fastest-Slowest")]),
        LineBreak(), Button("Back", piece_view_mode, [Argument("subtype", subtype)]),
    ])

@route
def piece_graph_menu(state: State, subtype: str) -> Page:
    return Page(state, [
        Header(f"{subtype} graphs"),
        Button("Line Chart (split over time)", line_chart, [Argument("subtype", subtype)]),
        Button("Bar Graph (times per split range)", bar_graph, [Argument("subtype", subtype)]),
        LineBreak(), Button("Back", piece_view_mode, [Argument("subtype", subtype)]),
    ])

# ---------------------------------------------------------------- VIEW: steady state
@route
def view_steady(state: State) -> Page:
    return Page(state, [
        Header("View Steady State"),
        Button("View Time", steady_order, [Argument("category", "steady"), Argument("subtype", "Time")]),
        Button("View Distance", steady_order, [Argument("category", "steady"), Argument("subtype", "Distance")]),
        Button("View Intervals", steady_order, [Argument("category", "interval"), Argument("subtype", "")]),
        LineBreak(), back_home(),
    ])

@route
def steady_order(state: State, category: str, subtype: str) -> Page:
    return Page(state, [
        Header("Sort by"),
        Button("Newest-Oldest", show_list, [Argument("category", category), Argument("subtype", subtype), Argument("order", "Newest-Oldest")]),
        Button("Fastest-Slowest", show_list, [Argument("category", category), Argument("subtype", subtype), Argument("order", "Fastest-Slowest")]),
        LineBreak(), Button("Back", view_steady),
    ])

# ---------------------------------------------------------------- VIEW: lifts / cross / recovery
@route
def view_cross(state: State) -> Page:
    return Page(state, [
        Header("View Cross-Training"),
        Button("View Bike", view_sorted_category, [Argument("category", "cross"), Argument("subtype", "Bike")]),
        Button("View Run", view_sorted_category, [Argument("category", "cross"), Argument("subtype", "Run")]),
        Button("View Swim", view_sorted_category, [Argument("category", "cross"), Argument("subtype", "Swim")]),
        LineBreak(), back_home(),
    ])

@route
def view_sorted_category(state: State, category: str, subtype: str) -> Page:
    return Page(state, [
        Header(f"{CATEGORY_TITLES[category]} {subtype}".strip()),
        Button("Newest-Oldest", show_list, [Argument("category", category), Argument("subtype", subtype), Argument("order", "Newest-Oldest")]),
        Button("Shortest-Longest", show_list, [Argument("category", category), Argument("subtype", subtype), Argument("order", "Shortest-Longest")]),
        LineBreak(), back_home(),
    ])

# ---------------------------------------------------------------- shared list page
@route
def show_list(state: State, category: str, subtype: str, order: str) -> Page:
    state.last_order = order                    # modifies state.last_order
    items = sort_workouts(matching(state, category, subtype), order)
    title = f"{CATEGORY_TITLES[category]} {subtype} - from {order.replace('-', ' to ')}"
    content = [Header(title.replace("  ", " "))]
    content.append(workout_table(items, category) if items else Text("Nothing logged yet."))
    content += [LineBreak(), back_home()]
    return Page(state, content)

# ---------------------------------------------------------------- graphs (text-based)
@route
def line_chart(state: State, subtype: str) -> Page:
    items = sorted(matching(state, "piece", subtype), key=lambda w: w.date)
    items = [w for w in items if to_seconds(w.split) < BAD_TIME]   # skip unreadable splits
    content = [Header(f"{subtype}: split over time"),
               Text("Longer bar = faster split.")]
    if items:
        slowest = max(to_seconds(w.split) for w in items)
        rows = [["Date", "Split", ""]]
        for w in items:
            length = int(40 * (slowest - to_seconds(w.split)) / max(slowest, 1) * 10) + 1
            rows.append([w.date, w.split, "█" * min(length, 60)])
        content.append(Table(rows))
    else:
        content.append(Text("Nothing logged yet."))
    content += [LineBreak(), Button("Back", piece_graph_menu, [Argument("subtype", subtype)])]
    return Page(state, content)

@route
def bar_graph(state: State, subtype: str) -> Page:
    items = [w for w in matching(state, "piece", subtype) if to_seconds(w.split) < BAD_TIME]
    content = [Header(f"{subtype}: number of times per split range")]
    if items:
        # Count how many workouts fall in each 5-second split range.
        # (type annotation dict[str, int] = keys are range labels, values are counts)
        buckets: dict[str, int] = {}
        for w in items:
            s = to_seconds(w.split)
            low = int(s // 5) * 5                      # 5-second buckets
            label = f"{low // 60}:{low % 60:02d}-{(low + 5) // 60}:{(low + 5) % 60:02d}"
            buckets[label] = buckets.get(label, 0) + 1   # .get(key, 0) = 0 if label is new
        rows = [["Split range", "Times", ""]]
        for label in sorted(buckets):
            rows.append([label, str(buckets[label]), "█" * buckets[label]])
        content.append(Table(rows))
    else:
        content.append(Text("Nothing logged yet."))
    content += [LineBreak(), Button("Back", piece_graph_menu, [Argument("subtype", subtype)])]
    return Page(state, content)

# ---------------------------------------------------------------- run
start_server(State([], ["2k", "6k", "2x10'"], "", "Newest-Oldest"))
