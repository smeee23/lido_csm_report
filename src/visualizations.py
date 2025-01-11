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
from utils import create_output_file, format_op_ids, ATTEST_METRICS

node_colors = ["red", "yellow", "orange", "purple", "green"]

def create_metric_page(pdf_path, node_operator, metric_name, description, figure_buffers, metric_data, date):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=32, bottomMargin=32)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=10
    )
    
    description_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=7,
        leading=14,
        spaceAfter=10
    )
    # Create description paragraph
    desc_para = Paragraph(description, description_style)

    # Convert buffer to ReportLab Image
    if figure_buffers[0]:
        figure_buffer = figure_buffers[0]
        figure_buffer.seek(0)
        image1 = Image(figure_buffer, width=5.25*inch, height=3.15*inch)
    else: image1 = None
    
    if figure_buffers[1]:
        figure_buffer = figure_buffers[1]
        figure_buffer.seek(0)
        image2 = Image(figure_buffer, width=5.25*inch, height=3.15*inch)
    else: image2 = None

    if metric_name in ATTEST_METRICS:
        tag = "per val"
    # Create table data
    table_data = [
        ['Metric', 'Value', 'Z-Score', 'Description'],
        ['CSM Operators Avg', metric_data['mean'], '',''],
        ['CSM Operators Median', metric_data['median'], '', ''],
        ['Standard Deviation', metric_data['std_dev'], '', ''],
        ['# Validators', metric_data['validatorCount'], '', ''],
        ['Total Attestations', metric_data['totalUniqueAttestations'], '', '']
    ]

    if metric_name in ATTEST_METRICS:
        table_data.insert(1, [format_label(metric_name).replace("Per Validator", ""), metric_data['per_val'], metric_data['zscore_per_val'], desc_para])
        table_data.insert(2, ['% Total Attestations', f"{metric_data['attest_pct']}%", metric_data['zscore_attest_pct'], ''])
    else:
        table_data.insert(1, [format_label(metric_name).replace("Average", ""), metric_data['metric'], metric_data['zscore_metric'], desc_para])

    # Create the table with the description column
    table = Table(table_data, colWidths=[1.5*inch, 1.25*inch, 1.25*inch, 3*inch])
    table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Only color first 3 columns
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (2, -1), 'CENTER'),
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Grid only for first 3 columns
        
        # Description column styling
        ('SPAN', (3, 1), (3, -1)),  # Merge all cells in description column
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
        ('VALIGN', (3, 1), (3, -1), 'TOP'),
    ]))
    
    # Build the PDF content
    content = [
        Paragraph(f"{node_operator[4:]} - {format_label(metric_name)} Analysis for {date.replace("_", " - ")}", title_style),
        image1,
        Spacer(1, 20),
        image2,
        Spacer(1, 20),
        table
    ]
    
    doc.build(content)

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
    output_file = create_output_file(format_op_ids(operator_ids), variable, date, type_report="histogram", module="CSM")
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
    
    output_file = create_output_file(format_op_ids(operator_ids), variable, date, type_report="time_series", module="CSM")
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
    elif "_" in date:
        date = date.replace("_", " - ")
    

    return f"{formatted_string.replace("avg", "Average")} {graph_type} {date}" 

def format_label(metric):
    # Remove the first 6 characters if the string starts with "perVal"
    if metric.startswith("perVal"):
        metric = metric[6:]
    
    metric = metric
    # Add a space before each capital letter
    formatted_string = generate_spaces(metric)
    
    if "Average" in formatted_string:
        return formatted_string
    return f"{formatted_string} Per Validator" 

def generate_spaces(s):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', s).replace("avg", "Average").replace("sum", "")