import matplotlib.pyplot as plt
import seaborn as sns

def plot_scatter(data, variable, operator_ids, date=None, title="Operator Variable Ratings Over Time"):
    highlighted_ratings = []
    highlighted_operators = []
    other_ratings = []
    other_operators = []

    # Filter data for the specific date if provided
    if date:
        data = {date: data[date]} if date in data else {}

    for current_date, operators in data.items():
        for operator, metrics in operators.items():
            if variable in metrics and metrics[variable] is not None:
                if any(f"Operator {id} -" in operator for id in operator_ids):
                    highlighted_operators.append(operator)
                    highlighted_ratings.append(metrics[variable])
                else:
                    other_operators.append(operator)
                    other_ratings.append(metrics[variable])

    # Create the scatter plot
    plt.figure(figsize=(10, 6))

    # Plot other operators in black
    plt.scatter(other_ratings, [date] * len(other_ratings), color="black", label="Other Operators")

    # Plot highlighted operators in red
    plt.scatter(highlighted_ratings, [date] * len(highlighted_ratings), color="red", label="Highlighted Operators")


    # Add labels and title
    plt.title(title)
    plt.ylabel("Date")
    plt.xlabel(variable)
    plt.legend()
    plt.tight_layout()

    # Save or show plot
    output_file = f"visuals/scatter_plot_{variable}_{date}.png" if date else "visuals/scatter_plot.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Plot saved to {output_file}")

def plot_line(data, variable, operator_ids, title="Default Line Plot Title"):
    """
    Plots a line graph for a single variable across operators and time.

    Args:
        data (dict): The data in the format {date: {operator: {variable: value}}}.
        variable (str): The variable to plot.
        title (str): Title of the plot.
    """
    operator_names = {}
    
    for date, operators in data.items():
        for operator, metrics in operators.items():
            if any(f"Operator {node_id} -" in operator for node_id in operator_ids):
                if variable in metrics and metrics[variable] is not None:
                    if operator not in operator_names:
                        operator_names[operator] = {"dates": [], "values": []}
                    operator_names[operator]["dates"].append(date)
                    operator_names[operator]["values"].append(metrics[variable])
    
    plt.figure(figsize=(12, 6))
    
    # Plot each operator's data
    for operator, values in operator_names.items():
        plt.plot(values["dates"], values["values"], marker='o', label=operator)
    
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(variable)
    plt.legend(title="Operators")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("visuals/scatter_line_test", dpi=300, bbox_inches="tight")