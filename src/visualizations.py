from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from reportlab.lib.units import inch
import io
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from logger_config import logger
from utils import create_output_file, format_op_ids

node_colors = ["red", "yellow", "orange", "purple", "green"]

def create_metric_page(pdf_path, node_operator, metric_name, description, figure, metric_data):
    """
    Creates a PDF page with metric analysis for a node operator.
    
    Args:
        pdf_path: Output PDF file path
        node_operator: Name of the node operator
        metric_name: Name of the metric being analyzed
        description: 1-2 paragraph description of the metric
        figure: matplotlib figure object
        metric_data: Dict containing metric values and statistics
    """
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    
    description_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        spaceAfter=20
    )
    
    # Convert matplotlib figure to ReportLab Image
    img_buffer = io.BytesIO()
    figure.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    image = Image(img_buffer, width=7*inch, height=4.2*inch)
    
    # Create table data
    table_data = [
        ['Metric', 'Value', 'Z-Score'],
        ['Raw Metric', metric_data['metric'], metric_data['metric_zscore']],
        ['Per Validator', metric_data['per_validator'], metric_data['per_validator_zscore']],
        ['Operator Average', metric_data['operator_avg'], metric_data['operator_avg_zscore']],
        ['All Operators Mean', metric_data['all_operators_mean'], ''],
        ['All Operators Median', metric_data['all_operators_median'], ''],
        ['All Operators Mode', metric_data['all_operators_mode'], ''],
        ['Standard Deviation', metric_data['std_dev'], '']
    ]
    
    table = Table(table_data, colWidths=[2.5*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    # Build the PDF content
    content = [
        Paragraph(f"{node_operator} - {metric_name} Analysis", title_style),
        Paragraph(description, description_style),
        image,
        Spacer(1, 20),
        table
    ]
    
    doc.build(content)

# Example usage:
def generate_metric_report(node_operator, metric_data_dict):
    """
    Generate PDF report pages for each metric.
    
    Args:
        node_operator: Name of the node operator
        metric_data_dict: Dictionary containing metric data and figures
    """
    for metric_name, data in metric_data_dict.items():
        output_path = f"{node_operator}_{metric_name}_analysis.pdf"
        create_metric_page(
            output_path,
            node_operator,
            metric_name,
            data['description'],
            data['figure'],
            data['metrics']
        )

def plot_histogram(data, variable, operator_ids, variant="per_val", date=None):
    highlighted_ratings = []
    other_ratings = []

    # If a list of dates is provided, compute the average over those dates
    if isinstance(date, list) or date is None:
        # Get the average ratings for the given operator_ids and dates
        highlighted_ratings, other_ratings, date = get_average_ratings_for_dates(data, variable, operator_ids, date)
    elif date:
        if date in data:
            for operator, metrics in data[date].items():
                if variable in metrics and metrics[variable][variant] is not None:
                    if any(f"Operator {id} -" in operator for id in operator_ids):
                        highlighted_ratings.append(metrics[variable][variant])
                    else:
                        other_ratings.append(metrics[variable][variant])
    

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

def plot_line(data, variable, operator_ids, variant="per_val", agg_data=None):
    if agg_data:
        for date in data:
            # exclude compound dates e.g. 2024-12-25_2024-12-27
            if date in agg_data and "_" not in date: 
                data[date].update(agg_data[date])

    operator_names = {}
    
    for date, operators in data.items():
        for operator, metrics in operators.items():
            if(
                any(f"Operator {node_id} -" in operator for node_id in operator_ids) or 
                operator in ["Lido", "Lido Community Staking Module"]
            ):
                if variable in metrics and metrics[variable][variant] is not None and "_" not in date:
                    if operator not in operator_names:
                        operator_names[operator] = {"dates": [], "values": []}
                    operator_names[operator]["dates"].append(date)
                    operator_names[operator]["values"].append(metrics[variable][variant])
    
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

def get_average_ratings_for_dates(data, variable, operator_ids, variant="per_val", date=None):
    highlighted_ratings = []
    other_ratings = []
    operator_counts = {}
    operator_sums = {}

    # If date is None, use all available dates in the data
    # exclude compound dates e.g. 2024-12-25_2024-12-27
    valid_dates = [d for d in list(data.keys()) if "_" not in d]
    if date is None: dates = valid_dates
    else: dates = date

    for current_date in dates:
        if current_date in data and "_" not in current_date:
            for operator, metrics in data[current_date].items():
                if variable in metrics and metrics[variable][variant] is not None:
                    if operator not in operator_counts:
                        operator_counts[operator] = 0
                        operator_sums[operator] = 0

                    operator_counts[operator] += 1
                    operator_sums[operator] += metrics[variable][variant]

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

def generate_spaces(s):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', s).replace("avg", "Average")