from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import io
from utils import create_output_file, format_op_ids, ATTEST_METRICS, DESCRIPTIONS
import os
from visualizations import create_metric_page

class ReportHandler:
    def __init__(self, operator_ids, data_handler, module="CSM"):
        self.base_path = os.path.join("reports", module)
        self.operator_ids = operator_ids
        self.dh = data_handler
        self.module = module

    def generate_report(self):

        for date, operators in self.dh.node_data.items():
                for id, metrics in operators.items():
                    if any([f" {op_id} -" in id for op_id in self.operator_ids]):
                        for key, value in metrics.items():
                            if date == "2024-12-25_2024-12-27" and key in DESCRIPTIONS.keys():
                                #print(key, value)
                                pdf_path = create_output_file(
                                                id=format_op_ids(self.operator_ids), 
                                                variable=key, 
                                                date=date, 
                                                type_report="report", 
                                                module=self.module, 
                                                ext="pdf"
                                            )
                                description = DESCRIPTIONS[key]
                                histo_path = create_output_file(
                                                id=format_op_ids(self.operator_ids), 
                                                variable=key, 
                                                date=date, 
                                                type_report="histogram", 
                                                module=self.module, 
                                                file_name=None
                                            )
                                
                                time_series_path = create_output_file(
                                                id=format_op_ids(self.operator_ids), 
                                                variable=key, 
                                                date=date, 
                                                type_report="time_series", 
                                                module=self.module, 
                                                file_name=None
                                            )
                                try:
                                    with open(histo_path, 'rb') as f:
                                        histo_buffer = io.BytesIO(f.read())
                                except:
                                    histo_buffer = None

                                try:
                                    with open(time_series_path, 'rb') as f:
                                        ts_buffer = io.BytesIO(f.read())
                                except:
                                    ts_buffer = None

                                if key in ATTEST_METRICS: stat_type = "per_val"
                                else: stat_type = "metric"

                                metric_data = {**(self.dh.node_stats[date][key][stat_type]) , **(self.dh.node_data[date][id][key])}                              
                                metric_data['validatorCount'] = self.dh.node_data[date][id]['validatorCount']['metric']
                                metric_data['totalUniqueAttestations'] = self.dh.node_data[date][id]['totalUniqueAttestations']['metric']
                                metric_data = {k: f"{v:.{3}f}".rstrip('0').rstrip('.') if isinstance(v, float) else v for k, v in metric_data.items()}

                                create_metric_page(
                                    pdf_path=pdf_path, 
                                    node_operator=id, 
                                    metric_name=key, 
                                    description=description, 
                                    figure_buffers=[histo_buffer, ts_buffer], 
                                    metric_data=metric_data,
                                    date=date
                                )
