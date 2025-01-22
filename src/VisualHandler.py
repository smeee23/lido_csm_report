from visualizations import plot_histogram, plot_line, plot_zscores, comparison_plot, gauge_plot
from utils import DESCRIPTIONS

class VisualHandler:
    def __init__(self, operator_ids, data_handler):
            self.operator_ids = operator_ids
            self.dh = data_handler

    def generate_histograms(self, node_data, date=None, sdvt_data={}, curated_module_data={}):
        for id in self.operator_ids:
            for variable, meta_data in DESCRIPTIONS.items():
                variant = meta_data['variant']
                avg = self.dh.node_stats[date][variable][variant]["mean"]
                median = self.dh.node_stats[date][variable][variant]["median"]
                print(f"{variable} {avg} {median}")

                comparison_plot(node_data=node_data, avg=avg, median=median, variable=variable, operator_ids=[id], variant=variant, date=date)  
                plot_zscores(node_data=node_data, variable=variable, operator_ids=[id], variant=variant, date=date)        
                for dist_type in ["all", "csm", "sdvt", "cur"]:
                    plot_histogram(node_data=node_data, variable=variable, operator_ids=[id], variant=variant, date=date, sdvt_data=sdvt_data, curated_module_data=curated_module_data, dist_type=dist_type)

    def generate_time_series(self, data, agg_data=None):
        for id in self.operator_ids:
            plot_line(data=data, variable="avgValidatorEffectiveness", operator_ids=[id], variant="metric", agg_data=agg_data)
            plot_line(data=data, variable="avgInclusionDelay", operator_ids=[id], variant="metric", agg_data=agg_data)
            plot_line(data=data, variable="avgCorrectness", operator_ids=[id], variant="metric", agg_data=agg_data)
            plot_line(data=data, variable="avgAttesterEffectiveness", operator_ids=[id], variant="metric", agg_data=agg_data)
            plot_line(data=data, variable="sumMissedAttestations", operator_ids=[id], variant="per_val", agg_data=agg_data)
            plot_line(data=data, variable="sumWrongHeadVotes", operator_ids=[id], variant="per_val", agg_data=agg_data)
            plot_line(data=data, variable="sumWrongTargetVotes", operator_ids=[id], variant="per_val", agg_data=agg_data)
            plot_line(data=data, variable="avgProposerEffectiveness", operator_ids=[id], variant="metric", agg_data=agg_data)
             