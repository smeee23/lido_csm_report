from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import io
from utils import create_output_file, format_op_ids
import os

class ReportHandler:
    def __init__(self, module="CSM"):
        self.base_path = os.path.join("reports", module)

    def generate_report(self, operator_ids, module="CSM"):
        report_path = create_output_file(format_op_ids(operator_ids), "avgAttesterEffectiveness", date=None, type_plot="report", module="CSM", file_name="report.pdf")
        image_path =  os.path.join(self.base_path, format_op_ids(operator_ids), "histogram", "avgAttesterEffectiveness_2024-12-24_2024-12-27.png")
    
        # PDF settings
        page_width, page_height = letter
        margin = 50  # Margin from the top and sides

        # Desired image width based on page size and margin
        image_width = page_width - 2 * margin
        aspect_ratio = 10 / 6  # Width / Height from plt.figure(figsize=(10, 6))
        image_height = image_width / aspect_ratio

        c = canvas.Canvas(report_path, pagesize=letter)


        # Add some text at the top with a margin
        c.setFont("Helvetica", 12)
        c.drawString(margin, page_height - margin, "Sample PDF Report with Existing Graphs")

        # Add the graph image, ensuring it retains the correct aspect ratio
        c.drawImage(image_path, x=margin, y=page_height - margin - image_height, 
                    width=image_width, height=image_height)

        # Save the PDF
        c.save()

