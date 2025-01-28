from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageBreak, Frame, PageTemplate, Paragraph, Table, TableStyle, Image, Spacer, HRFlowable
from reportlab.lib.units import inch
from datetime import datetime
import io
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from logger_config import logger
from utils import create_output_file, format_op_ids, ATTEST_METRICS, format_label, generate_spaces, get_average_ratings_for_dates, format_title
import numpy as np
import pandas


node_colors = ["red", "yellow", "orange", "purple", "green"]

def create_metric_page(pdf_path, node_operator, metric_name, description, figure_buffers, metric_data, date):
    # Define the page size and margins
    PAGE_WIDTH, PAGE_HEIGHT = letter
    MARGIN = 72

    # Create the document
    doc = BaseDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    # Define frames for the top and bottom halves of the page
    top_frame = Frame(
        MARGIN,
        PAGE_HEIGHT / 2,  # Start halfway down
        PAGE_WIDTH - 2 * MARGIN,
        PAGE_HEIGHT / 2 - MARGIN,  # Height of top half
        id="top",
    )
    bottom_frame = Frame(
        MARGIN,
        MARGIN,
        PAGE_WIDTH - 2 * MARGIN,
        PAGE_HEIGHT / 2 - MARGIN,  # Height of bottom half
        id="bottom",
    )

    def on_page(canvas, doc):
        # Footer
        footer_text = metric_name
        page_number_text = f"Page {doc.page}"
        canvas.setFont("Helvetica", 10)
        canvas.drawString(MARGIN, 0.5 * inch, footer_text)
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 0.5 * inch, page_number_text)

    page_template = PageTemplate(id="TwoFrame", frames=[top_frame, bottom_frame], onPage=on_page)
    doc.addPageTemplates([page_template])

    # Styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=10,
        alignment=1,
    )
    
    description_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=7,
        leading=14,
        spaceAfter=10
    )

    figure_style = ParagraphStyle(
        'CustomFigure',
        parent=styles['Italic'],
        fontSize=5,
        alignment=1,
    )

    # Create description paragraph
    desc_para = Paragraph(description, description_style)

    # Convert buffer to ReportLab Image
    images = []
    for buffer in figure_buffers:
        if buffer:
            figure_buffer = buffer
            figure_buffer.seek(0)
            images.append(Image(figure_buffer, width=5.5*inch, height=3.3*inch, hAlign='CENTER'))
        else: images.append(None)

    if metric_name in ATTEST_METRICS:
        tag = "per val"
    # Create table data
    table_data = [
        ['Metric', 'Value', 'Z-Score', 'Description'],
        ['# Validators', metric_data['validatorCount'], '-', ''],
        ['CSM Operators Avg', metric_data['mean'], '-',''],
        ['CSM Operators Median', metric_data['median'], '-', ''],
        ['CSM Standard Deviation', metric_data['std_dev'], '-', ''],
        ['Curated Avg', metric_data['mean_curated'], '-',''],
        ['Curated Median', metric_data['median_curated'], '-', ''],
        ['SDVT Avg', metric_data['mean_sdvt'], '-',''],
        ['SDVT Median', metric_data['median_sdvt'], '-', ''],
    ]

    if metric_name in ATTEST_METRICS:
        table_data.insert(1, ['Total Attestations', metric_data['totalUniqueAttestations'], '-', ''])
        table_data.insert(1, [f'Total {format_label(metric_name).replace("Per Validator", "")}', metric_data['sum'], '-', ''])
        table_data.insert(1, ['% Total Attestations', f"{metric_data['attest_pct']}%", metric_data['zscore_attest_pct'], ''])
        table_data.insert(1, [f"{format_label(metric_name).replace("Per Validator", "")} / Val / Day", metric_data['per_val'], metric_data['zscore_per_val'], desc_para])
        
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
    
    # Create content for the PDF
    content = []

    # Title and description
    content.append(Paragraph(f"{node_operator[4:]} - {format_label(metric_name)} Analysis for {date.replace('_', ' - ')}", title_style))

    content.append(table)

    # Spacer and line break
    content.append(Spacer(1, 30))

    content.append(images.pop())
    content.append(Paragraph("Figure 1: Metric Trends", figure_style))
    content.append(PageBreak())

    # Remaining images: 2 per page, separated by page breaks
    for i, img in enumerate(images):
        content.append(img)
        content.append(Paragraph(f"Figure {i + 2}: Additional Trends", figure_style))
        
        # Add a page break after every two images
        if (i + 1) % 2 == 0:
            content.append(PageBreak())
        else:
            content.append(Spacer(1, 50))
            content.append(HRFlowable(width="100%", thickness=2, color=colors.black))
            content.append(Spacer(1, 30))
    
    doc.build(content)

def footer(canvas, doc):
    """
    Draw a footer on each page.
    """
    PAGE_WIDTH, PAGE_HEIGHT = letter
    footer_text = "State of Nodes"
    page_number_text = f"Page {doc.page}"

    # Draw footer text
    canvas.setFont("Helvetica", 10)
    canvas.drawString(inch, 0.5 * inch, footer_text)

    # Draw page number on the right
    canvas.drawRightString(PAGE_WIDTH - inch, 0.5 * inch, page_number_text)

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

def generate_plotting_data(node_data, variable, operator_ids, variant="per_val", date=None, sdvt_data={}, curated_module_data={}):
    highlighted_ratings = []
    highlighted_zscores = []
    other_csm_ratings = []
    other_csm_zscores = []
    curated_module_ratings = []
    sdvt_ratings = []
    # If a list of dates is provided, compute the average over those dates
    if isinstance(date, list) or date is None:
        # Get the average ratings for the given operator_ids and dates
        highlighted_ratings, other_csm_ratings, date = get_average_ratings_for_dates(node_data, variable, operator_ids, date)
    elif date:
        for data in [node_data, sdvt_data, curated_module_data]:
            if date in data:
                for operator, metrics in data[date].items():
                    if variable in metrics and metrics[variable][variant] is not None:
                        if any(f"Operator {id} -" in operator for id in operator_ids):
                            highlighted_ratings.append(metrics[variable][variant])
                            if f"zscore_{variant}" in metrics[variable]:
                                highlighted_zscores.append(metrics[variable][f"zscore_{variant}"])
                        if "CSM Operator" in operator:
                            other_csm_ratings.append(metrics[variable][variant])
                            if f"zscore_{variant}" in metrics[variable]:
                                other_csm_zscores.append(metrics[variable][f"zscore_{variant}"])
                        elif "- Lido SimpleDVT Module" in operator:
                            sdvt_ratings.append(metrics[variable][variant])
                        elif "- Lido" in operator:
                            curated_module_ratings.append(metrics[variable][variant])

    if len(highlighted_ratings) != len(operator_ids):
        logger.error(f"Plot not drawn b/c {variable} not found for all operator_ids {operator_ids}")
        return
    
    return {
        "highlighted_ratings": highlighted_ratings,
        "highlighted_zscores": highlighted_zscores,
        "other_csm_ratings": other_csm_ratings,
        "other_csm_zscores": other_csm_zscores,
        "curated_module_ratings": curated_module_ratings,
        "sdvt_ratings": sdvt_ratings
        }

def plot_histogram(node_data, variable, operator_ids, variant="per_val", date=None, sdvt_data={}, curated_module_data={}, dist_type='all'):
    
    plotting_data = generate_plotting_data(
        node_data, 
        variable, 
        operator_ids, 
        variant, 
        date, 
        sdvt_data, 
        curated_module_data
    )
    if plotting_data:
        highlighted_ratings = plotting_data["highlighted_ratings"]
        highlighted_zscores = plotting_data["highlighted_zscores"]
        other_csm_ratings = plotting_data["other_csm_ratings"]
        other_csm_zscores = plotting_data["other_csm_zscores"]
        curated_module_ratings = plotting_data["curated_module_ratings"]
        sdvt_ratings = plotting_data["sdvt_ratings"]
        
        # Create the histogram
        plt.figure(figsize=(10, 6))
        _, bins = np.histogram(curated_module_ratings + other_csm_ratings + sdvt_ratings, bins='auto')

        if dist_type == 'csm':
            sns.histplot(other_csm_ratings, bins=bins, color="blue", label="CSM Operators")
        elif dist_type == 'sdvt':
            sns.histplot(sdvt_ratings, bins=bins, color="green", label="SDVT Operators")
        elif dist_type == 'cur':
            sns.histplot(curated_module_ratings, bins=bins, color="yellow", label="Curated Module")
        else:
            sns.histplot(curated_module_ratings + other_csm_ratings + sdvt_ratings, bins=bins, color="yellow", label="Curated Module")
            sns.histplot(other_csm_ratings + sdvt_ratings, bins=bins, color="green", label="SDVT Operators")
            sns.histplot(other_csm_ratings, bins=bins, color="blue", label="CSM Operators")

        # Plot highlighted operators in red
        for i in range(0, len(operator_ids)):
            color_index = i % len(node_colors)
            id = operator_ids[i]
            plt.scatter(highlighted_ratings[i], [0] , color=node_colors[color_index], label=f"CSM Operator {id}  |  {highlighted_ratings[i]:.6g}")

        # Add labels and title
        label = format_label(variable)
        title = format_title(metric=variable, date=None, graph_type="Distribution")
        plt.title(title, fontsize=18)  # Increase font size for the title
        plt.xlabel(label, fontsize=14)  # Increase font size for the x-axis label
        plt.ylabel("Operator Count", fontsize=14)  # Increase font size for the y-axis label

        # Adjust the legend font size
        plt.legend(fontsize=12)

        # Increase tick label size
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)

        plt.tight_layout()
        # Save or show plot
        output_file = create_output_file(format_op_ids(operator_ids), variable, date, type_report="histogram", module="CSM", dist_type=dist_type)
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()
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
    
    plt.figure(figsize=(10, 6))
    
    # Plot each operator's data
    for operator, values in operator_names.items():
        # Convert dates to datetime objects for sorting
        sorted_dates_values = sorted(
            zip(values["dates"], values["values"]),
            key=lambda x: datetime.strptime(x[0], "%Y-%m-%d")  # Adjust date format as needed
        )
        sorted_dates, sorted_values = zip(*sorted_dates_values)

        name = operator.replace("- Lido Community Staking Module", "")
        if name == "Lido Community Staking Module": name = "CSM Operators"
        elif name == "Lido": name = "Lido (All)"
        plt.plot(sorted_dates, sorted_values, label=name)
    
    title = format_title(metric=variable, date=None, graph_type="Time Series")
    label = generate_spaces(variable)

    plt.title(title, fontsize=18)  
    plt.xlabel("Date", fontsize=14)  
    plt.ylabel(label, fontsize=14)  

    # Adjust the legend font size
    plt.legend(fontsize=12)

    # Increase tick label size
    plt.xticks(rotation=45, ha="right", fontsize=12)
    plt.yticks(fontsize=12)

    plt.grid(True)
    plt.tight_layout()
    
    output_file = create_output_file(format_op_ids(operator_ids), variable, date, type_report="time_series", module="CSM")
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Plot saved to {output_file}")

#Voilin-box
def comparison_plot(node_data, avg, median, variable, operator_ids, variant="per_val", date=None, sdvt_data={}, curated_module_data={}):
    plotting_data = generate_plotting_data(
        node_data, 
        variable, 
        operator_ids, 
        variant, 
        date, 
        sdvt_data, 
        curated_module_data
    )

    if not plotting_data:
        return None
    
    highlighted_ratings = plotting_data["highlighted_ratings"]
    other_csm_ratings = plotting_data["other_csm_ratings"]

    fig, ax = plt.subplots(figsize=(10, 6))
    
    
    # Create violin plot
    sns.violinplot(data=other_csm_ratings, color='lightgray', inner='box')

    for i, rating in enumerate(highlighted_ratings):
        color = f'C{i}' 
        plt.scatter(0, highlighted_ratings[0], color='red', 
                s=100, zorder=3, label=f"CSM Operator {operator_ids[i]}  |  {highlighted_ratings[i]:.6g}")
    
    # Add mean and median lines
    plt.axhline(y=avg, color='blue', 
                linestyle='--', label='CSM Average')
    plt.axhline(y=median, color='green', 
                linestyle='--', label='CSM Median')
    
    label = format_label(variable)
    title = format_title(metric=variable, date=None, graph_type="Voilin-Box")
    plt.title(title, fontsize=18)
    plt.ylabel(label, fontsize=14)
    plt.legend(fontsize=12)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    output_file = create_output_file(format_op_ids(operator_ids), variable, date, type_report="voilin_box", module="CSM", dist_type="voilin_box")
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Plot saved to {output_file}")

def plot_zscores(node_data, variable, operator_ids, variant="per_val", date=None, sdvt_data={}, curated_module_data={}):
    plotting_data = generate_plotting_data(
        node_data, 
        variable, 
        operator_ids, 
        variant, 
        date, 
        sdvt_data, 
        curated_module_data
    )
    
    if not plotting_data:
        return None
    
    highlighted_zscores = plotting_data["highlighted_zscores"]
    other_csm_zscores = plotting_data["other_csm_zscores"]
    
    # Create the plot with full space utilization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Generate points for the normal distribution curve
    z_range = np.linspace(-3, 3, 100)
    normal_dist = np.exp(-(z_range**2)/2) / np.sqrt(2*np.pi)
    
    # Plot the normal distribution curve
    plt.plot(z_range, normal_dist, 'b-', alpha=0.5, label='Normal Distribution')
    
    # Add shaded regions for different z-score ranges
    plt.fill_between(z_range, normal_dist, where=(z_range >= -1) & (z_range <= 1),
                     color='green', alpha=0.2)
    plt.fill_between(z_range, normal_dist, where=(z_range >= -2) & (z_range <= 2),
                     color='yellow', alpha=0.1)
    plt.fill_between(z_range, normal_dist, where=(z_range >= -3) & (z_range <= 3),
                     color='red', alpha=0.05)
    
    # Plot vertical lines for each highlighted z-score
    for i, z_score in enumerate(highlighted_zscores):
        color = f'C{i}'
        plt.axvline(x=z_score, color=color, linestyle='--',
                    label=f'CSM Operator {operator_ids[i]} | z={z_score:.3f})')
    
    # Add reference lines at standard deviations
    for sd in [-2, -1, 0, 1, 2]:
        plt.axvline(x=sd, color='gray', linestyle=':', alpha=0.3)
    
    # Add labels and title
    title = format_title(metric=variable, date=None, graph_type="Z-Score Distribution")
    plt.title(title, fontsize=18)  # Increase font size for the title
    plt.xlabel('Standard Deviations from Mean', fontsize=14)
    plt.ylabel('Density', fontsize=14)
    
    plt.legend(loc='upper left', fontsize=12)
    # Increase tick label size
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    # Add grid for better readability
    plt.grid(True, alpha=0.3)
    
    # Set x-axis limits and ticks
    plt.xlim(-3, 3)
    plt.xticks(np.arange(-3, 4, 1))
    
    plt.tight_layout()
    
    output_file = create_output_file(format_op_ids(operator_ids), variable, date, type_report="zscore_dist", module="CSM", dist_type="zscore")
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Plot saved to {output_file}")

    