from visualizations import plot_histogram, plot_line

class VisualHandler:
    def __init__(self, operator_ids):
            self.operator_ids = operator_ids

    def generate_histograms(self, data, date=None):
        for id in self.operator_ids:
            plot_histogram(data=data, variable="avgValidatorEffectiveness", operator_ids=[id], variant="metric", date=date)
            plot_histogram(data=data, variable="avgInclusionDelay", operator_ids=[id], variant="metric", date=date)
            plot_histogram(data=data, variable="avgInclusionDelay", operator_ids=[id], variant="metric", date=date)
            plot_histogram(data=data, variable="avgCorrectness", operator_ids=[id], variant="metric", date=date)
            plot_histogram(data=data, variable="avgAttesterEffectiveness", operator_ids=[id], variant="metric", date=date)
            plot_histogram(data=data, variable="sumMissedAttestations", operator_ids=[id], variant="per_val", date=date)
            plot_histogram(data=data, variable="sumWrongHeadVotes", operator_ids=[id], variant="per_val", date=date)
            plot_histogram(data=data, variable="sumWrongTargetVotes", operator_ids=[id], variant="per_val", date=date)
            plot_histogram(data=data, variable="sumLateSourceVotes", operator_ids=[id], variant="per_val", date=date)
            plot_histogram(data=data, variable="avgProposerEffectiveness", operator_ids=[id], variant="metric", date=date)

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
             