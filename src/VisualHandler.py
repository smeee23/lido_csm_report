from visualizations import plot_histogram, plot_line

class VisualHandler:
    def __init__(self, operator_ids):
            self.operator_ids = operator_ids

    def generate_histograms(self, data, date=None):
        for id in self.operator_ids:
            plot_histogram(data=data, variable="avgValidatorEffectiveness", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="avgInclusionDelay", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="avgInclusionDelay", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="avgCorrectness", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="avgAttesterEffectiveness", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="perValMissedAttestations", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="perValWrongHeadVotes", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="perValWrongTargetVotes", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="perValLateSourceVotes", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="perValInclusionDelay", operator_ids=[id], date=date)
            plot_histogram(data=data, variable="avgProposerEffectiveness", operator_ids=[id], date=date)

    def generate_time_series(self, data, date=None, agg_data=None):
        for id in self.operator_ids:
            plot_line(data=data, variable="avgValidatorEffectiveness", operator_ids=[id], agg_data=agg_data)
            plot_line(data=data, variable="avgInclusionDelay", operator_ids=[id], agg_data=agg_data)
            plot_line(data=data, variable="avgCorrectness", operator_ids=[id], agg_data=agg_data)
            plot_line(data=data, variable="avgAttesterEffectiveness", operator_ids=[id], agg_data=agg_data)
            plot_line(data=data, variable="perValMissedAttestations", operator_ids=[id], agg_data=agg_data)
            plot_line(data=data, variable="perValWrongHeadVotes", operator_ids=[id], agg_data=agg_data)
            plot_line(data=data, variable="perValWrongTargetVotes", operator_ids=[id], agg_data=agg_data)
            plot_line(data=data, variable="perValInclusionDelay", operator_ids=[id], agg_data=agg_data)
            plot_line(data=data, variable="avgProposerEffectiveness", operator_ids=[id], agg_data=agg_data)
             