import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from logger_config import logger

node_colors = ["red", "yellow", "orange", "purple", "green"]

def plot_histogram(data, variable, operator_ids, date=None):
    highlighted_ratings = []
    other_ratings = []

    # If a list of dates is provided, compute the average over those dates
    if isinstance(date, list) or date is None:
        # Get the average ratings for the given operator_ids and dates
        highlighted_ratings, other_ratings, date = get_average_ratings_for_dates(data, variable, operator_ids, date)
    elif date:
        if date in data:
            for operator, metrics in data[date].items():
                if variable in metrics and metrics[variable] is not None:
                    if any(f"Operator {id} -" in operator for id in operator_ids):
                        highlighted_ratings.append(metrics[variable])
                    else:
                        other_ratings.append(metrics[variable])
    

    if len(highlighted_ratings) != len(operator_ids):
        logger.error(f"Plot not drawn b/c {variable} not found for all operator_ids {operator_ids}")
        return
    
    # Create the histogram
    plt.figure(figsize=(10, 6))

    # Plot histogram for other operators in blue
    sns.histplot(other_ratings, color="blue", label="CSM Operators")

    # Plot highlighted operators in red
    for i in range(0, len(operator_ids)):
        color_index = i % len(node_colors)
        id = operator_ids[i]
        plt.scatter(highlighted_ratings[i], [1] , color=node_colors[color_index], label=f"CSM Operator {id}  |  {highlighted_ratings[i]:.6g}")

    # Add labels and title
    label = format_label(variable)
    title = format_title(metric=variable, date=date, graph_type="Distribution")
    plt.title(title)
    plt.xlabel(label)
    plt.ylabel("Operator Count")
    plt.legend()
    plt.tight_layout()

    # Save or show plot
    output_file = create_output_file(format_op_ids(operator_ids), variable, date, type_plot="histogram", module="CSM")
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    logger.info(f"Plot saved to {output_file}")

def plot_line(data, variable, operator_ids, agg_data=None):
    if agg_data:
        for date in data:
            if date in agg_data:
                data[date].update(agg_data[date])

    operator_names = {}
    
    for date, operators in data.items():
        for operator, metrics in operators.items():
            if(
                any(f"Operator {node_id} -" in operator for node_id in operator_ids) or 
                operator in ["Lido", "Lido Community Staking Module"]
            ):
                if variable in metrics and metrics[variable] is not None:
                    if operator not in operator_names:
                        operator_names[operator] = {"dates": [], "values": []}
                    operator_names[operator]["dates"].append(date)
                    operator_names[operator]["values"].append(metrics[variable])
    
    plt.figure(figsize=(12, 6))
    
    # Plot each operator's data
    for operator, values in operator_names.items():
        name = operator.replace("- Lido Community Staking Module", "")
        if name == "Lido Community Staking Module": name = "CSM Operators"
        elif name == "Lido": name = "Lido (All)"
        plt.plot(values["dates"], values["values"], marker='o', label=name)
    
    title = format_title(metric=variable, date=None, graph_type="Time Series")
    label = generate_spaces(variable)

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(label)
    plt.legend(title="Operators")
    plt.grid(True)
    plt.tight_layout()
    
    output_file = create_output_file(format_op_ids(operator_ids), variable, date, type_plot="time_series", module="CSM")
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    logger.info(f"Plot saved to {output_file}")

def get_average_ratings_for_dates(data, variable, operator_ids, date=None):
    highlighted_ratings = []
    other_ratings = []
    operator_counts = {}
    operator_sums = {}

    # If date is None, use all available dates in the data
    if date is None: dates = list(data.keys())
    else: dates = date

    for current_date in dates:
        if current_date in data:
            for operator, metrics in data[current_date].items():
                if variable in metrics and metrics[variable] is not None:
                    if operator not in operator_counts:
                        operator_counts[operator] = 0
                        operator_sums[operator] = 0

                    operator_counts[operator] += 1
                    operator_sums[operator] += metrics[variable]

    # Calculate averages
    for operator in operator_counts:
        avg = operator_sums[operator] / operator_counts[operator]
        if any(f"Operator {id} -" in operator for id in operator_ids):
            highlighted_ratings.append(avg)
        else:
            other_ratings.append(avg)
    return highlighted_ratings, other_ratings, dates

def format_title(metric, date, graph_type="Distribution"):
    # Remove the first 6 characters if the string starts with "perVal"
    if metric.startswith("perVal"):
        metric = metric[6:]
    
    # Add a space before each capital letter
    formatted_string = generate_spaces(metric)
    
    if date is None:
        date = ""
    elif isinstance(date, list) and len(date) > 1:
        date = f"{len(date)}day MVA {date[len(date)-1]}"
    

    return f"{formatted_string.replace("avg", "Average")} {graph_type} {date}" 

def format_label(metric):
    # Remove the first 6 characters if the string starts with "perVal"
    if metric.startswith("perVal"):
        metric = metric[6:]
    
    # Add a space before each capital letter
    formatted_string = generate_spaces(metric)
    
    return f"{formatted_string} / Num Validators" 

def format_op_ids(operator_ids):
    if len(operator_ids) == 1:
        return str(operator_ids[0])
    
    s = ""
    for id in operator_ids:
        s = f"{s}_{id}"
    
    return s

def create_output_file(id, variable, date="", type_plot="histogram", module="CSM"):

    if isinstance(date, list) and len(date) > 1:
        date = f"{date[0]}_{date[len(date)-1]}"

    # Define the output file path using os.path.join
    output_file = os.path.join("graphs", module, str(id), type_plot, f"{variable}_{date}.png")
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    return output_file

def generate_spaces(s):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', s).replace("avg", "Average")